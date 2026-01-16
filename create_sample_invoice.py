from PIL import Image, ImageDraw, ImageFont

def create_invoice(filename, invoice_no, hsn_code, description, taxable_value, rate_percent):
    # Calculate amounts
    tax_amount = taxable_value * (rate_percent / 100)
    total_amount = taxable_value + tax_amount
    
    # Create white canvas
    img = Image.new('RGB', (800, 1000), color='white')
    d = ImageDraw.Draw(img)

    # Fonts
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        header_font = ImageFont.truetype("arial.ttf", 24)
        bold_font = ImageFont.truetype("arialbd.ttf", 20)
    except:
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        bold_font = ImageFont.load_default()

    # Header
    d.text((50, 50), "INVOICE", fill="black", font=header_font)
    
    # Vendor
    d.text((50, 100), "Vendor Name:", fill="gray", font=font)
    d.text((250, 100), "Omaverse AI Solutions", fill="black", font=bold_font)
    d.text((50, 130), "Vendor GSTIN:", fill="gray", font=font)
    d.text((250, 130), "09ABCDE1234F1Z5", fill="black", font=font)
    
    # Details
    d.text((50, 180), "Invoice Number:", fill="gray", font=font)
    d.text((250, 180), invoice_no, fill="black", font=font)
    d.text((50, 210), "Invoice Date:", fill="gray", font=font)
    d.text((250, 210), "January 16, 2026", fill="black", font=font)
    
    # Recipient
    d.text((50, 260), "Recipient:", fill="gray", font=font)
    d.text((250, 260), "Test Recipient Ltd.", fill="black", font=bold_font)
    d.text((50, 290), "Recipient GSTIN:", fill="gray", font=font)
    d.text((250, 290), "07QRUVW5678G2Z9", fill="black", font=font)
    
    # Line
    d.line((50, 330, 750, 330), fill="black", width=2)
    
    # Items
    d.text((50, 350), "Description:", fill="gray", font=font)
    d.text((250, 350), description, fill="black", font=font)
    
    d.text((50, 390), "HSN/SAC Code:", fill="gray", font=font)
    d.text((250, 390), str(hsn_code), fill="black", font=bold_font)
    
    d.text((50, 430), "Taxable Value:", fill="gray", font=font)
    d.text((250, 430), f"₹{taxable_value:,.2f}", fill="black", font=font)
    
    d.text((50, 470), "IGST Rate:", fill="gray", font=font)
    d.text((250, 470), f"{rate_percent}%", fill="black", font=bold_font)
    
    d.text((50, 510), "Tax Amount:", fill="gray", font=font)
    d.text((250, 510), f"₹{tax_amount:,.2f}", fill="black", font=font)
    
    # Line
    d.line((50, 550, 750, 550), fill="black", width=2)
    
    d.text((50, 570), "Grand Total:", fill="black", font=header_font)
    d.text((250, 570), f"₹{total_amount:,.2f}", fill="black", font=header_font)

    img.save(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    # Test Case 1: Air Conditioning (HSN 8415) at 28% (Validating against new 18%)
    create_invoice(
        "invoice_test_8415.jpg", 
        "INV-TEST-001", 
        8415, 
        "Air Conditioning Machine", 
        100000, 
        28
    )

    # Test Case 2: Tractors (HSN 8701) at 12% (Validating against new 5%)
    create_invoice(
        "invoice_test_8701.jpg", 
        "INV-TEST-002", 
        8701, 
        "Agricultural Tractor (< 1800cc)", 
        500000, 
        12
    )

    # Test Case 3: Shampoo (HSN 3305) at 18% (Validating against new 5%)
    create_invoice(
        "invoice_test_3305.jpg", 
        "INV-TEST-003", 
        3305, 
        "Shampoos and Hair Oils", 
        10000, 
        18
    )
