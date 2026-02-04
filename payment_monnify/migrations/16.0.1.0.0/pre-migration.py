# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Update existing payment transactions to use the new provider code."""
    cr.execute("""
        UPDATE payment_transaction
        SET provider_code = 'payment_monnify'
        WHERE provider_code = 'monnify';
    """)
    
    cr.execute("""
        UPDATE payment_provider
        SET code = 'payment_monnify'
        WHERE code = 'monnify';
    """)
