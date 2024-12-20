import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse

def compare(request):
    return render(request, "reconciliation/upload.html")


def upload_files(request):
    if request.method == "POST":
        file1 = request.FILES.get("file1")
        file2 = request.FILES.get("file2")

        if not file1 or not file2:
            return JsonResponse({"error": "Both files are required!"}, status=400)
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
        except Exception as e:
            return JsonResponse({"error": f"Error reading files: {str(e)}"}, status=400)

        required_columns = ["Date", "Debit", "Credit"]
        for col in required_columns:
            if col not in df1.columns or col not in df2.columns:
                return JsonResponse({"error": f"Missing required column: {col}"}, status=400)

        # Standardize and clean the data
        df1["Date"] = pd.to_datetime(df1["Date"], errors="coerce")
        df2["Date"] = pd.to_datetime(df2["Date"], errors="coerce")
    
        df1["Debit"] = pd.to_numeric(df1["Debit"], errors="coerce").round(2)
        df1["Credit"] = pd.to_numeric(df1["Credit"], errors="coerce").round(2)
        df2["Debit"] = pd.to_numeric(df2["Debit"], errors="coerce").round(2)
        df2["Credit"] = pd.to_numeric(df2["Credit"], errors="coerce").round(2)

        # Reconciliation logic
        matched_rows = []
        unmatched_in_file1 = []
        unmatched_in_file2 = []

        # Loop through rows in file1 and match with rows in file2
        for _, row1 in df1.iterrows():
            date = row1["Date"]
            debit = row1["Debit"]
            credit = row1["Credit"]

            if pd.notna(debit) and pd.isna(credit):  # Debit exists, no Credit
                match = df2[
                    (df2["Date"].dt.date <= date.date()) &  # Direct comparison without calling .date()
                    (df2["Date"].dt.month == date.month) & 
                    (df2["Date"].dt.year == date.year) & 
                    (df2["Credit"].sub(debit).abs() <= 1.00)
                ]
            elif pd.notna(credit) and pd.isna(debit):  # Credit exists, no Debit
                match = df2[
                    (df2["Date"].dt.date <= date.date()) &  # Direct comparison without calling .date()
                    (df2["Date"].dt.month == date.month) & 
                    (df2["Date"].dt.year == date.year) & 
                    (df2["Debit"].sub(credit).abs() <= 1.00)
                ]
            else:
                match = pd.DataFrame()

            if not match.empty:
                matched_rows.append(row1.to_dict())
            else:
                unmatched_in_file1.append(row1.to_dict())

        # Find unmatched rows in file2
        for _, row2 in df2.iterrows():
            date = row2["Date"]
            debit = row2["Debit"]
            credit = row2["Credit"]

            if pd.notna(debit) and pd.isna(credit):  # Debit exists, no Credit
                match = df1[
                    (df1["Date"].dt.date >= date.date()) &  # Direct comparison without calling .date()
                    (df1["Date"].dt.month == date.month) & 
                    (df1["Date"].dt.year == date.year) & 
                    (df1["Credit"].sub(debit).abs() <= 1.00)
                ]
            elif pd.notna(credit) and pd.isna(debit):  # Credit exists, no Debit
                match = df1[
                    (df1["Date"].dt.date >= date.date()) &  # Direct comparison without calling .date()
                    (df1["Date"].dt.month == date.month) & 
                    (df1["Date"].dt.year == date.year) & 
                    (df1["Debit"].sub(credit).abs() <= 1.00)
                ]
            else:
                match = pd.DataFrame()

            if match.empty:
                unmatched_in_file2.append(row2.to_dict())

        # Format the dates in unmatched_in_file1 and unmatched_in_file2
        for row in unmatched_in_file1:
            if "Date" in row and pd.notna(row["Date"]):
                row["Date"] = pd.to_datetime(row["Date"]).strftime('%d/%m/%Y')

        for row in unmatched_in_file2:
            if "Date" in row and pd.notna(row["Date"]):
                row["Date"] = pd.to_datetime(row["Date"]).strftime('%d/%m/%Y')

        # Render the result page with unmatched rows
        return render(request, "reconciliation/result.html", {
            "unmatched_in_file1": unmatched_in_file1,
            "unmatched_in_file2": unmatched_in_file2,
        })

    return render(request, "reconciliation/upload.html")
