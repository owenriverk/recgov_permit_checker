# Simple test script
from Skimmer import send_alert  # Replace with actual import

# Test data
test_permits = ["Permit A - March 30", "Permit B - April 15"]

# Run the test
print("Testing email alert...")
result = send_alert(test_permits)
print(f"Email sent: {result}")