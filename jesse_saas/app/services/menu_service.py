from app.models import MenuItem
from app.extensions import db
from app.services.upload_service import UploadService

class MenuService:
    @staticmethod
    def get_items(client_id):
        return MenuItem.query.filter_by(client_id=client_id).order_by(MenuItem.category.desc(), MenuItem.name).all()

    @staticmethod
    def create_item(client, form_data, files):
        """
        Creates a new menu item for a client.
        """
        name = form_data.get('name')
        if not name:
            raise ValueError("Item name is required")

        price = 0.0
        try:
            raw_price = str(form_data.get('price', 0)).replace(',', '.')
            price = float(raw_price)
        except ValueError:
            pass

        original_price = None
        if form_data.get('original_price'):
            try:
                raw_op = str(form_data['original_price']).replace(',', '.')
                original_price = float(raw_op)
            except ValueError:
                pass
            
        category = form_data.get('category', 'Other')
        category = form_data.get('category', 'Other')
        description = form_data.get('description')
        allergy_info = form_data.get('allergy_info')
        labels = form_data.get('labels') # Comma-separated string
        
        image_url = None
        if files and 'image' in files:
            file = files['image']
            image_url = UploadService.upload(file, folder='menu', public_id_prefix=f"{client.public_id}")
        
        item = MenuItem(
            client_id=client.id,
            name=name,
            price=price,
            original_price=original_price,
            labels=labels,
            category=category,
            description=description,
            image_url=image_url,
            allergy_info=allergy_info,
            is_available=True
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def update_item(item_id, form_data, files, client_id_check=None):
        """
        Updates an existing menu item.
        Optional client_id_check ensures ownership.
        """
        item = MenuItem.query.get_or_404(item_id)
        
        if client_id_check and item.client_id != client_id_check:
            raise PermissionError("Unauthorized access to menu item")
            
        if 'name' in form_data:
            item.name = form_data['name']
        
        if 'price' in form_data:
            try:
                raw_price = str(form_data['price']).replace(',', '.')
                item.price = float(raw_price)
            except ValueError:
                pass

        if 'original_price' in form_data:
            val = form_data['original_price']
            if val and str(val).strip() != '':
                try:
                    raw_op = str(val).replace(',', '.')
                    item.original_price = float(raw_op)
                except ValueError:
                    item.original_price = None
            else:
                item.original_price = None

        if 'labels' in form_data:
            item.labels = form_data['labels']
        
        if 'category' in form_data:
            item.category = form_data['category']
            
        if 'description' in form_data:
            item.description = form_data['description']

        if 'allergy_info' in form_data:
            item.allergy_info = form_data['allergy_info']
        
        if files and 'image' in files:
            file = files['image']
            if file.filename != '':
                url = UploadService.upload(file, folder='menu', public_id_prefix=f"{item.client.public_id}")
                if url:
                     item.image_url = url

        db.session.commit()
        return item

    @staticmethod
    def toggle_availability(item_id, client_id_check=None):
        item = MenuItem.query.get_or_404(item_id)
        if client_id_check and item.client_id != client_id_check:
             raise PermissionError("Unauthorized")
        
        item.is_available = not item.is_available
        db.session.commit()
        return item.is_available

    @staticmethod
    def delete_item(item_id, client_id_check=None):
        item = MenuItem.query.get_or_404(item_id)
        if client_id_check and item.client_id != client_id_check:
             raise PermissionError("Unauthorized")
        
        db.session.delete(item)
        db.session.commit()
