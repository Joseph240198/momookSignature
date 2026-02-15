using System;
using System.Drawing;
using System.Windows.Forms;
using wgssSTU; // Wacom STU COM namespace

namespace SignCapture_wacom
{
    public partial class Form1 : Form
    {

        private Tablet m_tablet;
        private ICapability m_capability;
        private Bitmap m_bitmap;
        private Graphics m_gfx;

        // Use alias to avoid conflict with wgssSTU.Rectangle
        private System.Drawing.Rectangle btnOk;
        private System.Drawing.Rectangle btnClear;
        public Form1()
        {
            InitializeComponent();
            ConnectTablet();
        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }
        private void ConnectTablet()
        {
            try
            {
                UsbDevices usbDevices = new UsbDevices();
                if (usbDevices.Count == 0)
                {
                    MessageBox.Show("No Wacom STU tablet found.");
                    return;
                }

                IUsbDevice usbDevice = usbDevices[0];
                m_tablet = new Tablet();
                IErrorCode ec = m_tablet.usbConnect(usbDevice, true);

                if (ec.value != 0)
                {
                    MessageBox.Show($"Failed to connect to tablet. Error code: {ec.value}");
                    return;
                }

                m_capability = m_tablet.getCapability();
                CreateTabletUI();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error connecting to tablet: " + ex.Message);
            }
        }

        private void CreateTabletUI()
        {
            // Create a bitmap the size of the tablet screen
            m_bitmap = new Bitmap(m_capability.screenWidth, m_capability.screenHeight);
            m_gfx = Graphics.FromImage(m_bitmap);
            m_gfx.Clear(Color.White);

            // Define simple buttons
            btnOk = new System.Drawing.Rectangle(10, 10, 100, 50);
            btnClear = new System.Drawing.Rectangle(120, 10, 100, 50);

            // Draw buttons
            m_gfx.FillRectangle(Brushes.LightGreen, btnOk);
            m_gfx.DrawRectangle(Pens.Black, btnOk);
            m_gfx.DrawString("OK", new Font("Arial", 16), Brushes.Black, btnOk.X + 20, btnOk.Y + 10);

            m_gfx.FillRectangle(Brushes.LightCoral, btnClear);
            m_gfx.DrawRectangle(Pens.Black, btnClear);
            m_gfx.DrawString("Clear", new Font("Arial", 16), Brushes.Black, btnClear.X + 10, btnClear.Y + 10);

            // Prepare image for tablet
            ProtocolHelper helper = new ProtocolHelper();
            ushort productId = m_tablet.getProductId();
            encodingFlag encFlag = (encodingFlag)helper.simulateEncodingFlag(productId, 0);
            encodingMode mode;

            if ((encFlag & (encodingFlag.EncodingFlag_16bit | encodingFlag.EncodingFlag_24bit)) != 0)
                mode = m_tablet.supportsWrite() ? encodingMode.EncodingMode_24bit_Bulk : encodingMode.EncodingMode_24bit;
            else
                mode = encodingMode.EncodingMode_1bit;

            bool useColor = (mode == encodingMode.EncodingMode_16bit_Bulk ||
                 mode == encodingMode.EncodingMode_16bit ||
                 mode == encodingMode.EncodingMode_24bit_Bulk ||
                 mode == encodingMode.EncodingMode_24bit);

            byte[] imageData = (byte[])helper.resizeAndFlatten(
                BitmapToByteArray(m_bitmap),
                0, 0,
                (ushort)m_bitmap.Width, (ushort)m_bitmap.Height,
                (ushort)m_capability.screenWidth, (ushort)m_capability.screenHeight,
                useColor,
                wgssSTU.Scale.Scale_Fit,
                0, 0
               );

            m_tablet.writeImage((byte)mode, imageData);
        }

        private byte[] BitmapToByteArray(Bitmap bmp)
        {
            using (System.IO.MemoryStream stream = new System.IO.MemoryStream())
            {
                bmp.Save(stream, System.Drawing.Imaging.ImageFormat.Png);
                return stream.ToArray();
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            base.OnFormClosing(e);
            if (m_tablet != null)
            {
                m_tablet.disconnect();
            }
        }
    }
}
