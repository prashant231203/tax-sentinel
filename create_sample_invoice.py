from PIL import Image, ImageDraw, ImageFont
import os

def create_invoice_image():
    # Create white canvas
    img = Image.new('RGB', (800, 1000), color='white')
    d = ImageDraw.Draw(img)

    # Simple default font
    try:
        # Attempt to use a standard font usually available on Windows
        font = ImageFont.truetype("arial.ttf", 20)
        header_font = ImageFont.truetype("arial.ttf", 24)
        bold_font = ImageFont.truetype("arialbd.ttf", 20)
    except:
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        bold_font = ImageFont.load_default()

    # Data from user screenshot
    # Mimicking the layout
    d.text((50, 50), "INVOICE", fill="black", font=header_font)
    
    # Vendor
    d.text((50, 100), "Vendor Name:", fill="gray", font=font)
    d.text((250, 100), "Omaverse AI Solutions Pvt. Ltd.", fill="black", font=bold_font)
    
    d.text((50, 130), "Vendor GSTIN:", fill="gray", font=font)
    d.text((250, 130), "09ABCDE1234F1Z5 (Uttar Pradesh)", fill="black", font=font)
    
    # Details
    d.text((50, 180), "Invoice Number:", fill="gray", font=font)
    d.text((250, 180), "INV/2026/001", fill="black", font=font)
    
    d.text((50, 210), "Invoice Date:", fill="gray", font=font)
    d.text((250, 210), "Jan 15, 2026", fill="black", font=font)
    
    # Recipient
    d.text((50, 260), "Recipient:", fill="gray", font=font)
    d.text((250, 260), "Scrapeuncle Pvt. Ltd. (New Delhi)", fill="black", font=bold_font)
    
    d.text((50, 290), "Recipient GSTIN:", fill="gray", font=font)
    d.text((250, 290), "07QRUVW5678G2Z9", fill="black", font=font)
    
    # Line
    d.line((50, 330, 750, 330), fill="black", width=2)
    
    # Items
    d.text((50, 350), "Service Description:", fill="gray", font=font)
    d.text((250, 350), "AI-Native ERP Implementation Consulting", fill="black", font=font)
    
    d.text((50, 390), "HSN/SAC Code:", fill="gray", font=font)
    d.text((250, 390), "998311", fill="black", font=bold_font)
    
    d.text((50, 430), "Taxable Value:", fill="gray", font=font)
    d.text((250, 430), "₹1,00,000", fill="black", font=font)
    
    d.text((50, 470), "IGST Rate Charged:", fill="gray", font=font)
    d.text((250, 470), "12%", fill="red", font=bold_font) # Highlight the error visually? No, keep it black like a real invoice usually.
    
    d.text((50, 510), "Total IGST Amount:", fill="gray", font=font)
    d.text((250, 510), "₹12,000", fill="black", font=font)
    
    # Line
    d.line((50, 550, 750, 550), fill="black", width=2)
    
    d.text((50, 570), "Grand Total:", fill="black", font=header_font)
    d.text((250, 570), "₹1,12,000", fill="black", font=header_font)

    img.save("sample_invoice.jpg")
    print("Created sample_invoice.jpg")

if __name__ == "__main__":
    create_invoice_image()
