from app.models import Client, InteractionLog
from config import Config

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
