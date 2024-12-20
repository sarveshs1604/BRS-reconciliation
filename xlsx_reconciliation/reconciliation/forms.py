from django import forms

class XLSXUploadForm(forms.Form):
    file1 = forms.FileField(label="Upload First XLSX File")
    file2 = forms.FileField(label="Upload Second XLSX File")
