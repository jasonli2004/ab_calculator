import yfinance as yf
import pandas as pd
import statsmodels.api as sm
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import sys

def fetch_sp500_returns(days=7):
    try:
        sp500_ticker = "^GSPC"
        end_date = datetime.today()
        start_date = end_date - timedelta(days=days)
        
        sp500_data = yf.download(sp500_ticker, start=start_date.strftime('%Y-%m-%d'), 
                                 end=end_date.strftime('%Y-%m-%d'))
        sp500_data['Daily Return'] = sp500_data['Close'].pct_change()
        sp500_returns = sp500_data['Daily Return'].dropna()
        print("SP500 data fetched successfully.")
        return sp500_returns
    except Exception as e:
        print(f"Error fetching SP500 data: {e}")
        sys.exit(1)

def calculate_alpha_beta(user_returns, sp500_returns):
    try:
        min_length = min(len(user_returns), len(sp500_returns))
        user_returns = user_returns[:min_length]
        sp500_returns = sp500_returns[:min_length]
        
        data = pd.DataFrame({
            'User': user_returns,
            'SP500': sp500_returns.values
        })
        
        X = sm.add_constant(data['SP500'])
        Y = data['User']
        
        model = sm.OLS(Y, X).fit()
        alpha, beta = model.params
        
        print(f"Calculated Alpha: {alpha:.6f}")
        print(f"Calculated Beta: {beta:.6f}")
        return alpha, beta
    except Exception as e:
        print(f"Error calculating Alpha and Beta: {e}")
        sys.exit(1)

def initialize_firebase():
    try:
        cred = credentials.Certificate('userab-7b795-firebase-adminsdk-aghkz-acbb3f611b.json')  # Update this path with firebase key
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase initialized successfully.")
        return db
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        sys.exit(1)

def push_to_firebase(db, alpha, beta, user_id):
    try:
        data = {
            'alpha': alpha,
            'beta': beta,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'user_id': user_id
        }
        db.collection('performance').add(data)
        print("Alpha and Beta pushed to Firebase successfully.")
    except Exception as e:
        print(f"Error pushing data to Firebase: {e}")
        sys.exit(1)

def main():
    sp500_returns = fetch_sp500_returns(days=7)
    
    user_returns = [0.005, -0.002, 0.010, -0.003, 0.007]

    user_id = 1
    
    alpha, beta = calculate_alpha_beta(user_returns, sp500_returns)
    
    db = initialize_firebase()
    
    push_to_firebase(db, alpha, beta, user_id)

if __name__ == "__main__":
    main()
