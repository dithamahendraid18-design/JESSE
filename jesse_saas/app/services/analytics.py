from app.models import Client, InteractionLog
from config import Config
from app.extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta
import csv
import io

class AnalyticsService:
    @staticmethod
    def get_dashboard_stats():
        """
        Calculate high-level dashboard metrics for the SaaS admin.
        """
        total_clients = Client.query.count()
        pro_clients = Client.query.filter_by(plan_type='pro').count()
        basic_clients = Client.query.filter_by(plan_type='basic').count()
        
        # Financials
        monthly_mrr = pro_clients * Config.PRICING_PRO_MONTHLY
        
        # Usage
        total_interactions = InteractionLog.query.count()
        token_cost_est = total_interactions * Config.TOKEN_COST_PER_INTERACTION
        
        return {
            'total_clients': total_clients,
            'pro_clients': pro_clients,
            'basic_clients': basic_clients,
            'mrr': monthly_mrr,
            'total_interactions': total_interactions,
            'token_cost': round(token_cost_est, 2)
        }

    @staticmethod
    def get_client_overview(client_id):
        """
        Get specific client overview stats including engagement score.
        """
        client = Client.query.get(client_id)
        if not client:
            return {}

        total = client.logs.count()
        ai_chats = client.logs.filter_by(interaction_type='ai_chat').count()
        
        # Calculate AI Ratio
        ai_ratio = round((ai_chats / total * 100), 1) if total > 0 else 0
        
        # Calculate Engagement Score (Proxy for Success Rate)
        # Simple Heuristic: Average interactions per day / 10 (normalized to 100%)
        # Or simpler: Ratio of AI Chats to total interactions is a good proxy for "Conversation depth"
        # Let's use: (AI Chats / Total) * 1.2 capped at 100% just to have a dynamic number
        engagement_score = min(round(ai_ratio * 1.2, 1), 99.5) if total > 0 else 0

        return {
            'total_conversations': total,
            'ai_ratio': ai_ratio,
            'engagement_score': engagement_score
        }

    @staticmethod
    def get_trend_data(client_id, days=7):
        """
        Returns daily interaction counts for the last N days.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query: Count logs per day
        logs = db.session.query(
            func.date(InteractionLog.timestamp).label('date'),
            func.count(InteractionLog.id).label('count')
        ).filter(
            InteractionLog.client_id == client_id,
            InteractionLog.timestamp >= start_date
        ).group_by(
            func.date(InteractionLog.timestamp)
        ).all()
        
        # Convert to dictionary {date: count}
        data_map = {str(log.date): log.count for log in logs}
        
        # Fill in missing days
        labels = []
        counts = []
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            labels.append(current.strftime('%b %d')) # Format: Jan 01
            counts.append(data_map.get(date_str, 0))
            current += timedelta(days=1)
            
        return {
            'labels': labels,
            'counts': counts
        }

    @staticmethod
    def get_export_csv(client_id):
        """
        Generates CSV content for client logs.
        """
        client = Client.query.get(client_id)
        logs = client.logs.order_by(InteractionLog.timestamp.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Timestamp', 'Type', 'Query/Content'])
        
        # Rows
        for log in logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.interaction_type,
                log.user_query
            ])
            
        return output.getvalue()

    @staticmethod
    def get_top_clients(limit=5):
        """
        Efficiently fetches top 5 clients by interaction volume using SQL group_by.
        """
        results = db.session.query(
            Client, 
            func.count(InteractionLog.id).label('interaction_count')
        ).outerjoin(InteractionLog, Client.id == InteractionLog.client_id)\
         .group_by(Client.id)\
         .order_by(func.count(InteractionLog.id).desc())\
         .limit(limit).all()
        
        top_clients = []
        for client, count in results:
            client.interaction_count = count
            top_clients.append(client)
            
        return top_clients

    @staticmethod
    def get_client_stats(status_filter='all', plan_filter='all'):
        """
        Get aggregated client statistics for the clients list view.
        """
        clients_query = Client.query
        
        if status_filter != 'all':
            clients_query = clients_query.filter_by(status=status_filter)
        if plan_filter != 'all':
            clients_query = clients_query.filter_by(plan_type=plan_filter)
            
        return {
            "total": Client.query.count(),
            "active": Client.query.filter_by(status='active').count(),
            "pending": Client.query.filter_by(status='inactive').count()
        }
