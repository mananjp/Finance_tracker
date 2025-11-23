# Finance Tracker with Item-Level Categorization

This is a personal finance tracker web app built with [Streamlit](https://streamlit.io/) that allows you to upload receipt images or paste receipt text. It automatically extracts individual expense items using EasyOCR and lets you categorize each item before saving it as an expense. It also supports manual expense entry and provides interactive dashboards for expense analysis.

---

## Features

- **OCR-based item extraction** using EasyOCR for fast, offline receipt scanning
- **Item-by-item review and editing** of parsed receipt items: Modify description, amount, and assign category individually
- **Manual expense entry** with category and date selection
- **Filter and view expenses** by category and source (OCR/manual)
- **Detailed statistics dashboard** with pie charts (category breakdown) and bar charts (source comparison)
- Expenses are saved locally in `expenses_data.json`

---

## Installation

1. Clone the repository or download the Python script `finance_tracker_easyocr.py`
2. Install required dependencies:

   ```bash
   pip install streamlit easyocr pillow pandas plotly numpy
   ```

3. Run the app:

   ```bash
   streamlit run finance_tracker_easyocr.py
   ```

---

## Usage

- **Scan Bill Tab:**  
  - Upload receipt images or paste text.  
  - Parsed items will be shown with editable fields: description, amount, and category.  
  - Select which items to save.  

- **Manual Entry Tab:**  
  - Manually add expenses with description, amount, category, and date.  

- **Expenses Tab:**  
  - View all recorded expenses.  
  - Filter by category and source.  
  - Delete expenses as needed.  

- **Statistics Tab:**  
  - Visualize total expenses, monthly trends, category distributions, and source comparisons.

---

## Receipt Parsing

The parser handles receipts that list items with descriptions followed by prices on the next line or in various common formats. You can edit any parsed item before saving.

---

## Limitations & Notes

- Currently uses **EasyOCR** for OCR recognition; works offline and fast.  
- OCR quality depends on receipt image clarity and format.

---

## License

This project is open-source and free to use under the Apache License.

---

## Acknowledgments

- Uses [EasyOCR](https://github.com/JaidedAI/EasyOCR) for OCR  
- Built with [Streamlit](https://streamlit.io/)  
- Visualization powered by [Plotly](https://plotly.com/python/)  

---

Enjoy effortless expense tracking with easy receipt scanning and detailed analytics! 🎉
