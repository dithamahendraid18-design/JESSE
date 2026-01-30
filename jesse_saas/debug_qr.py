import qrcode
import io
import sys

try:
    print("Testing JPEG generation...")
    img = qrcode.make("test")
    buf = io.BytesIO()
    
    # Try saving as JPEG
    try:
        img.save(buf, format='JPEG')
        print("Success saving as JPEG")
    except Exception as e:
        print(f"Failed saving as JPEG: {e}")

except Exception as e:
    print(f"General Error: {e}")
