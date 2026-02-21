using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using wgssSTU;

class Program
{
    static Tablet m_tablet;
    static ICapability m_capability;

    static List<IPenData> penDataList = new List<IPenData>();

    static System.Drawing.Rectangle btnOk;
    static System.Drawing.Rectangle btnClear;
    static System.Drawing.Rectangle btnCancel;

    static bool isPenDown = false;
    static int buttonAreaHeight = 40;

    static void Main(string[] args)
    {
        Console.WriteLine("Connecting...");

        UsbDevices usbDevices = new UsbDevices();
        if (usbDevices.Count == 0)
        {
            Console.WriteLine("No tablet found.");
            return;
        }
        try
        {
            m_tablet = new Tablet();
            m_tablet.usbConnect(usbDevices[0], true);

        }
        catch (System.Runtime.InteropServices.COMException ex)
        {
            Console.WriteLine("Error conectando tablet: " + ex.Message);
            return;
        }

        m_capability = m_tablet.getCapability();

        InitButtons();
        DrawInitialScreen();

        // Activar inking (fluido)
        m_tablet.setInkingMode(0x01);

        // Suscribirse a eventos
        ((ITabletEvents2_Event)m_tablet).onPenData += OnPenData;
        AppDomain.CurrentDomain.ProcessExit += OnProcessExit;

        Console.WriteLine("Ready.");
        System.Threading.Thread.Sleep(-1);
    }

    private static void OnProcessExit(object sender, EventArgs e)
    {
        Console.WriteLine("El programa se está cerrando...");

        if (m_tablet != null)
        {
            
        }
    }
    private static void ClearTabletScreen()
    {
        if (m_tablet == null)
        {  return; }

        m_tablet.setInkingMode(0x00);
        using (Bitmap bmp = new Bitmap(m_capability.screenWidth, m_capability.screenHeight))
        {
            using (Graphics g = Graphics.FromImage(bmp))
            {
                g.Clear(Color.White);
            }

            WriteBitmapToTablet(bmp);
        }
        m_tablet.setInkingMode(0x01);
    }
    static void InitButtons()
    {
        int y = m_capability.screenHeight - buttonAreaHeight + 5;
        int margin = 10;
        int spacing = 10;
        int btnWidth = 93;

        //(horizontal distance from left side screen, vertical distance from upper side, button width, button height)
        btnOk = new System.Drawing.Rectangle(margin, y, btnWidth, 30);
        btnClear = new System.Drawing.Rectangle(margin + btnWidth + spacing, y, 93, 30);
        btnCancel = new System.Drawing.Rectangle(margin + (btnWidth + spacing) * 2, y, 93, 30);
    }

    static void DrawInitialScreen()
    {
        m_tablet.setInkingMode(0x00);

        Bitmap bmp = new Bitmap(m_capability.screenWidth, m_capability.screenHeight);

        using (Graphics g = Graphics.FromImage(bmp))
        {
            g.Clear(Color.White);

            Pen pen = new Pen(Color.Black, 2);
            Font font = new Font("Arial", 16, FontStyle.Bold);

            StringFormat sf = new StringFormat();
            sf.Alignment = StringAlignment.Center;      // Horizontal
            sf.LineAlignment = StringAlignment.Center;  // Vertical

            // Línea divisoria
            g.DrawLine(pen, 2,
                m_capability.screenHeight - buttonAreaHeight,
                m_capability.screenWidth,
                m_capability.screenHeight - buttonAreaHeight);

            // OK
            g.FillRectangle(Brushes.LightGreen, btnOk);
            g.DrawRectangle(pen, btnOk);
            g.DrawString("OK", font, Brushes.Black, btnOk, sf);

            // Clear
            g.FillRectangle(Brushes.LightGreen, btnClear);
            g.DrawRectangle(pen, btnClear);
            g.DrawString("Clear", font, Brushes.Black, btnClear, sf);

            // Clear
            g.FillRectangle(Brushes.LightGreen, btnCancel);
            g.DrawRectangle(pen, btnCancel);
            g.DrawString("Cancel", font, Brushes.Black, btnCancel, sf);
        }

        WriteBitmapToTablet(bmp);

        m_tablet.setInkingMode(0x01);
    }

    private static void DisconnectTablet()
    {
        if (m_tablet == null) return;

        try
        {
            ClearTabletScreen();       // opcional
            m_tablet.setInkingMode(0); // apagar inking
            m_tablet.disconnect();     // desconectar seguro
            Console.WriteLine("Tablet desconectada correctamente.");
        }
        catch (Exception ex)
        {
            Console.WriteLine("Error al desconectar tablet: " + ex.Message);
        }
        finally
        {
            m_tablet = null;
        }
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
                Console.WriteLine("OK");
                Console.Out.Flush();
                ProcessSignature();
                DrawInitialScreen();
                ClearTabletScreen();
                penDataList.Clear();
                WriteStatus("OK");
                DisconnectTablet();
                Environment.Exit(0);
                return;
            }

            if (btnClear.Contains(p))
            {
                Console.WriteLine("Clear pressed!");
                penDataList.Clear();
                DrawInitialScreen();
                return;
            }

            if (btnCancel.Contains(p))
            {
                Console.WriteLine("CANCEL");
                Console.Out.Flush();
                penDataList.Clear();
                DrawInitialScreen();
                penDataList.Clear();
                WriteStatus("CANCEL");
                DisconnectTablet();
                Environment.Exit(0);
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

    public static void WriteStatus(string message)
    {
        try
        {
            string statusFilePath = "C:\\Users\\Jose A\\Desktop\\momook_signature\\Techlogs\\signature\\WacomStatus.txt";
            // Si existe, borrarlo
            if (File.Exists(statusFilePath))
            {
                File.Delete(statusFilePath);
            }

            // Crear y escribir la primera línea con el mensaje
            using (StreamWriter writer = new StreamWriter(statusFilePath, false)) // false = sobrescribir
            {
                writer.WriteLine(message);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("Error escribiendo status.txt: " + ex.Message);
        }
    }
    static void ProcessSignature()
    {
        /*
        Console.WriteLine("Signature captured.");
        Console.WriteLine($"Total points: {penDataList.Count}");

        foreach (var p in penDataList)
        {
            Console.WriteLine($"X:{p.x} Y:{p.y} P:{p.pressure}");
        }
        */
        if (penDataList.Count == 0)
            return;

        int width = m_capability.screenWidth;
        int height = m_capability.screenHeight - buttonAreaHeight;

        Bitmap bmp = new Bitmap(width, height);

        using (Graphics g = Graphics.FromImage(bmp))
        {
            g.Clear(Color.White);
            Pen pen = new Pen(Color.Black, 2);

            IPenData prev = null;

            foreach (var p in penDataList)
            {
                int x = p.x * width / m_capability.tabletMaxX;
                int y = p.y * m_capability.screenHeight / m_capability.tabletMaxY;

                if (prev != null)
                {
                    int prevX = prev.x * width / m_capability.tabletMaxX;
                    int prevY = prev.y * m_capability.screenHeight / m_capability.tabletMaxY;

                    if (y < height && prevY < height)
                        g.DrawLine(pen, prevX, prevY, x, y);
                }

                prev = p;
            }
        }

        string path = "C:\\Users\\Jose A\\Desktop\\momook_signature\\Techlogs\\signature\\signature.png";
        // Si ya existe, eliminarlo
        if (System.IO.File.Exists(path))
        {
            System.IO.File.Delete(path);
        }
        bmp.Save(path, System.Drawing.Imaging.ImageFormat.Png);
        penDataList.Clear();

        Console.WriteLine("SIGNATURE_SAVED");
        Console.WriteLine(path);
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
