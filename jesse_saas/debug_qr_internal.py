import qrcode
import sys

try:
    print("Generating QR...")
    img = qrcode.make("test")
    print(f"Type of img: {type(img)}")
    
    try:
        print("Attempting .convert('RGB')...")
        img_converted = img.convert("RGB")
        print("Convert success!")
    except AttributeError:
        print("AttributeError: Object has no attribute 'convert'")
        # Try finding the inner image
        if hasattr(img, '_img'):
             print("Found _img attribute, checking its type...")
             print(type(img._img))
    except Exception as e:
        print(f"Other error during convert: {e}")

except Exception as e:
    print(f"Setup error: {e}")
