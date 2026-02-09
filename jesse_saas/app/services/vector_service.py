import os
import requests
import json
from app.extensions import db
from app.models import MenuItem, MenuEmbedding
from sqlalchemy import func

class VectorService:
    @staticmethod
    def get_embedding(text, api_key=None):
        """
        Generates embedding using HuggingFace Inference API (all-MiniLM-L6-v2).
        Dimensions: 384
        """
        if not api_key:
            api_key = os.environ.get('HUGGINGFACE_API_KEY')
        
        if not api_key:
            print("VectorService Error: No HUGGINGFACE_API_KEY found.")
            return None

        # Model: all-MiniLM-L6-v2 is fast, free, and good for basic RAG
        model_id = "BAAI/bge-small-en-v1.5"
        api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # HF expects list of strings related to inputs usually, but raw string works for feature-extraction
        payload = {"inputs": [text], "options": {"wait_for_model": True}}
        
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                print(f"VectorService: HF Error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            
            # Response is a list of floats (the vector) directly, OR a list of lists if batch
            result = resp.json()
            
            # Helper to check if it's nested list (batch) or single list
            if isinstance(result, list):
                if isinstance(result[0], list):
                    return result[0] # Return first if batch
                return result # It's the vector itself
            
            return None
        except Exception as e:
            print(f"HF Embedding API Error: {e}")
            return None

    @staticmethod
    def sync_menu_embeddings(client_id):
        """
        Generates embeddings for all menu items of a client.
        This should be called explicitly (e.g., via a button or after csv import).
        """
        try:
            # 1. Get Client's API Key (or System Key)
            # Use strict Query to decouple from circular imports if possible, or just use Model
            from app.models import Client
            client = Client.query.get(client_id)
            if not client: return False
            
            # Use HuggingFace Key
            api_key = os.environ.get('HUGGINGFACE_API_KEY')
            
            if not api_key:
                print(f"Skipping sync for Client {client_id}: No API Key.")
                return False

            items = MenuItem.query.filter_by(client_id=client_id).all()
            count = 0
            
            for item in items:
                # 2. Construct Text Representation
                # "Name: Truffle Pasta. Category: Food. Price: $20. Desc: Delicious truffle sauce."
                text = f"Name: {item.name}. Category: {item.category or 'General'}. Price: {item.price}. Description: {item.description or ''}"
                
                # 3. Check if embedding exists
                embedding_entry = MenuEmbedding.query.filter_by(menu_item_id=item.id).first()
                
                # Optimization: In a real system, we'd check hash to see if update is needed. 
                # For now, we update if missing. To force update, user can clear table or we add a force flag.
                if embedding_entry:
                    continue 

                # 4. Generate & Save
                VectorService.upsert_item_embedding(item, api_key)
                count += 1
            
            db.session.commit()
            print(f"Synced {count} embeddings (new) for Client {client_id}")
            return True
        except Exception as e:
            print(f"Sync Error: {e}")
            return False
            
    @staticmethod
    def upsert_item_embedding(item, api_key=None):
        """
        Updates or creates embedding for a specific item.
        """
        try:
            if not api_key:
                api_key = os.environ.get('HUGGINGFACE_API_KEY')
                
            if not api_key: return False

            text = f"Name: {item.name}. Category: {item.category or 'General'}. Price: {item.price}. Description: {item.description or ''}"
            
            vector = VectorService.get_embedding(text, api_key)
            if not vector: return False
            
            # Check existing
            embedding_entry = MenuEmbedding.query.filter_by(menu_item_id=item.id).first()
            if embedding_entry:
                embedding_entry.embedding = vector
            else:
                new_emb = MenuEmbedding(menu_item_id=item.id, embedding=vector)
                db.session.add(new_emb)
            
            # We don't commit here to allow caller to manage transaction? 
            # safe to commit if called individually.
            db.session.commit() 
            return True
        except Exception as e:
            print(f"Upsert Error: {e}")
            return False

    @staticmethod
    def delete_item_embedding(item_id):
        try:
            MenuEmbedding.query.filter_by(menu_item_id=item_id).delete()
            db.session.commit()
            return True
        except:
            return False

    @staticmethod
    def search_menu(client_id, query, limit=5):
        """
        Hybrid Search:
        1. Vectors (Semantic)
        2. Fallback to SQL ILIKE (Keyword) if Vectors fail or return nothing.
        """
        items = []
        
        # --- STRATEGY 1: VECTOR SEARCH ---
        try:
            from app.models import Client
            # Use HF Key
            api_key = os.environ.get('HUGGINGFACE_API_KEY')
            
            if api_key:
                query_vector = VectorService.get_embedding(query, api_key)
                if query_vector:
                    # L2 distance search
                    results = db.session.query(MenuEmbedding, MenuItem).\
                        join(MenuItem).\
                        filter(MenuItem.client_id == client_id, MenuItem.is_available == True).\
                        order_by(MenuEmbedding.embedding.l2_distance(query_vector)).\
                        limit(limit).\
                        all()
                    
                    items = [r[1] for r in results]
                    if items: return items
                    
        except Exception as e:
            print(f"Vector Search Failed (Fallback to SQL): {e}")

        # --- STRATEGY 2: SQL KEYWORD FALLBACK ---
        # If we are here, Vector failed or returned empty.
        try:
            print(f"Executing SQL Fallback for query: {query}")
            # Split query into words and filter generic stopwords
            keywords = [w for w in query.split() if len(w) > 3] 
            
            if not keywords: return [] # Query too short/generic

            # Build OR query for each keyword against Name or Description
            sql_query = MenuItem.query.filter(MenuItem.client_id == client_id, MenuItem.is_available == True)
            
            conditions = []
            for kw in keywords:
                term = f"%{kw}%"
                conditions.append(MenuItem.name.ilike(term))
                conditions.append(MenuItem.description.ilike(term))
                conditions.append(MenuItem.category.ilike(term))
            
            from sqlalchemy import or_
            items = sql_query.filter(or_(*conditions)).limit(limit).all()
            return items
            
        except Exception as e:
            print(f"SQL Search Error: {e}")
            return []
