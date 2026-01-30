import qrcode
import qrcode.image.svg
import io
import sys

try:
    print("Testing SVG generation...")
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make("test_url", image_factory=factory)
    
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    
    content = buf.getvalue()
    if len(content) > 0 and b"<svg" in content:
        print("Success: SVG generated.")
    else:
        print(f"Failure: Content length {len(content)}, does not contain <svg")
        
except Exception as e:
    print(f"Error: {e}")
