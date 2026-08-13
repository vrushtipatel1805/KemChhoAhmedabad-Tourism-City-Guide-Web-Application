from app import app, db, RideBooking, Payment

def debug_completion():
    with app.app_context():
        # 1. Find the active ride for Rakesh Jain or any driver with an active ride
        # Screenshot shows 'Rakesh Jain' has a ride with 'Jay Patel'
        # Status should be ACCEPTED or ONGOING
        active_ride = RideBooking.query.filter(RideBooking.status.in_(['ACCEPTED', 'ONGOING'])).first()
        
        if not active_ride:
            print("No active ride found to debug.")
            return

        print(f"Found active ride: ID {active_ride.id}, Driver: {active_ride.driver_id}, Status: {active_ride.status}")
        
        # 2. Simulate the 'Complete' request
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['driver_id'] = active_ride.driver_id
                sess['username'] = "DebugDriver"
            
            print("Sending POST request to /api/driver/update_ride...")
            response = client.post('/api/driver/update_ride', json={
                'ride_id': active_ride.id,
                'action': 'complete'
            })
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Data: {response.get_json()}")
            
            if response.status_code == 200 and response.get_json().get('status') == 'success':
                print("SUCCESS: Ride marked as completed.")
                
                # Check Payment Status
                payment = Payment.query.filter_by(booking_id=active_ride.id, booking_type='ride').first()
                if payment:
                    print(f"Payment Status: {payment.payment_status} (Method: {payment.payment_method})")
                else:
                    print("No payment record found.")
            else:
                print("FAILURE: Request failed.")

if __name__ == "__main__":
    debug_completion()
