"""Software test fixtures are not analytical customer records."""
import pytest
import pandas as pd

@pytest.fixture
def customer():
    # A copy of the supplied first synthetic record, modified only within tests.
    return {'CustomerID':'TEST-ONLY','Gender':'Female','Age':34,'TenureMonths':12,
            'SubscriptionType':'Basic','MonthlyCharges':49.99,'TotalCharges':599.88,
            'ContractType':'Month-to-Month','SupportTickets':3,'PaymentMethod':'Credit Card','Churn':'Yes'}

@pytest.fixture
def frame(customer):
    return pd.DataFrame([customer])
