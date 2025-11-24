import requests

BASE_URL = 'http://127.0.0.1:5000/api'

def test_report():
    # Assuming Scan ID 2 exists from previous tests and has results
    scan_id = 2
    print(f"Downloading report for Scan {scan_id}...")
    
    res = requests.get(f'{BASE_URL}/reports/{scan_id}/download?format=html')
    
    if res.status_code == 200:
        print("Report downloaded successfully.")
        content = res.text
        if "<!DOCTYPE html>" in content and "Vulnerability Scan Report" in content:
            print("Report content verified (HTML).")
            # Save to file for manual inspection if needed
            with open('test_report.html', 'w') as f:
                f.write(content)
            print("Saved to test_report.html")
        else:
            print("Report content invalid.")
            print(content[:500])
        print(f"Failed to download report: {res.status_code}")
        print(res.text)

    # Test PDF
    print(f"Downloading PDF report for Scan {scan_id}...")
    res = requests.get(f'{BASE_URL}/reports/{scan_id}/download?format=pdf')
    
    if res.status_code == 200:
        print("PDF Report downloaded successfully.")
        if res.headers['Content-Type'] == 'application/pdf':
            print("Content-Type verified (application/pdf).")
            with open('test_report.pdf', 'wb') as f:
                f.write(res.content)
            print("Saved to test_report.pdf")
        else:
            print(f"Invalid Content-Type: {res.headers['Content-Type']}")
    else:
        print(f"Failed to download PDF report: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    test_report()
