using System;
using System.Collections.Generic;
using System.Drawing;
using wgssSTU;

class Program
{
    static Tablet m_tablet;
    static ICapability m_capability;

    static List<IPenData> penDataList = new List<IPenData>();

    static System.Drawing.Rectangle btnOk;
    static System.Drawing.Rectangle btnClear;

    static bool isPenDown = false;
    static int buttonAreaHeight = 70;

    static void Main(string[] args)
    {
        Console.WriteLine("Connecting...");

        UsbDevices usbDevices = new UsbDevices();
        if (usbDevices.Count == 0)
        {
            Console.WriteLine("No tablet found.");
            return;
        }

        m_tablet = new Tablet();
        m_tablet.usbConnect(usbDevices[0], true);
        m_capability = m_tablet.getCapability();

        InitButtons();
        DrawInitialScreen();

        // Activar inking (fluido)
        m_tablet.setInkingMode(0x01);

        // Suscribirse a eventos
        ((ITabletEvents2_Event)m_tablet).onPenData += OnPenData;

        Console.WriteLine("Ready.");
        System.Threading.Thread.Sleep(-1);
    }

    static void InitButtons()
    {
        int y = m_capability.screenHeight - buttonAreaHeight + 10;

        btnOk = new System.Drawing.Rectangle(30, y, 120, 50);
        btnClear = new System.Drawing.Rectangle(200, y, 120, 50);
    }

    static void DrawInitialScreen()
    {
        m_tablet.setInkingMode(0x00);

        Bitmap bmp = new Bitmap(m_capability.screenWidth, m_capability.screenHeight);

        using (Graphics g = Graphics.FromImage(bmp))
        {
            g.Clear(Color.White);

            // Línea divisoria
            g.DrawLine(Pens.Black,
                0,
                m_capability.screenHeight - buttonAreaHeight,
                m_capability.screenWidth,
                m_capability.screenHeight - buttonAreaHeight);

            // OK
            g.FillRectangle(Brushes.LightGreen, btnOk);
            g.DrawRectangle(Pens.Black, btnOk);
            g.DrawString("OK", new Font("Arial", 18),
                Brushes.Black, btnOk.X + 30, btnOk.Y + 10);

            // Clear
            g.FillRectangle(Brushes.LightCoral, btnClear);
            g.DrawRectangle(Pens.Black, btnClear);
            g.DrawString("Clear", new Font("Arial", 18),
                Brushes.Black, btnClear.X + 10, btnClear.Y + 10);
        }

        WriteBitmapToTablet(bmp);

        m_tablet.setInkingMode(0x01);
    }

    static void OnPenData(IPenData penData)
    {
        int pixelX = penData.x * m_capability.screenWidth / m_capability.tabletMaxX;
        int pixelY = penData.y * m_capability.screenHeight / m_capability.tabletMaxY;

        Point p = new Point(pixelX, pixelY);

        if (penData.sw != 0 && !isPenDown)
        {
            isPenDown = true;

            if (btnOk.Contains(p))
            {
                Console.WriteLine("OK pressed!");
                ProcessSignature();
                DrawInitialScreen();
                return;
            }

            if (btnClear.Contains(p))
            {
                Console.WriteLine("Clear pressed!");
                penDataList.Clear();
                DrawInitialScreen();
                return;
            }
        }

        // Solo guardar escritura si está en zona superior
        if (penData.sw != 0 &&
            pixelY < m_capability.screenHeight - buttonAreaHeight)
        {
            penDataList.Add(penData);
        }

        if (penData.sw == 0)
            isPenDown = false;
    }

    static void ProcessSignature()
    {
        Console.WriteLine("Signature captured.");
        Console.WriteLine($"Total points: {penDataList.Count}");

        foreach (var p in penDataList)
        {
            Console.WriteLine($"X:{p.x} Y:{p.y} P:{p.pressure}");
        }
    }

    private static void WriteBitmapToTablet(Bitmap bitmap)
    {
        ProtocolHelper helper = new ProtocolHelper();
        ushort productId = m_tablet.getProductId();
        encodingFlag encFlag = (encodingFlag)helper.simulateEncodingFlag(productId, 0);

        encodingMode mode = (encFlag & (encodingFlag.EncodingFlag_16bit | encodingFlag.EncodingFlag_24bit)) != 0
            ? (m_tablet.supportsWrite() ? encodingMode.EncodingMode_24bit_Bulk : encodingMode.EncodingMode_24bit)
            : encodingMode.EncodingMode_1bit;

        bool useColor = (mode == encodingMode.EncodingMode_16bit_Bulk ||
                         mode == encodingMode.EncodingMode_16bit ||
                         mode == encodingMode.EncodingMode_24bit_Bulk ||
                         mode == encodingMode.EncodingMode_24bit);

        byte[] imageData = (byte[])helper.resizeAndFlatten(
            BitmapToByteArray(bitmap),
            0, 0,
            (ushort)bitmap.Width, (ushort)bitmap.Height,
            (ushort)m_capability.screenWidth, (ushort)m_capability.screenHeight,
            useColor,
            Scale.Scale_Fit,
            0, 0
        );

        m_tablet.writeImage((byte)mode, imageData);
    }

    private static byte[] BitmapToByteArray(Bitmap bmp)
    {
        using (var stream = new System.IO.MemoryStream())
        {
            bmp.Save(stream, System.Drawing.Imaging.ImageFormat.Png);
            return stream.ToArray();
        }
    }

}
