#!/usr/bin/env python3
"""
Lose It! Email Parser
Extracts nutrition data from daily summary emails
"""

import re
from datetime import datetime
from bs4 import BeautifulSoup

def parse_loseit_email(html_content, subject=None):
    """Parse Lose It! daily report email"""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract date from subject or content
    date = datetime.now().strftime('%Y-%m-%d')
    if subject:
        date_match = re.search(r'([A-Za-z]+ \d{1,2}, \d{4})', subject)
        if date_match:
            date = datetime.strptime(date_match.group(1), '%B %d, %Y').strftime('%Y-%m-%d')
    
    # Find summary table
    data = {
        'date': date,
        'food_calories': None,
        'exercise_calories': None,
        'net_calories': None,
        'deficit': None,
        'weight': None,
        'meals': []
    }
    
    # Parse summary table
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[-1].get_text(strip=True)
                
                if 'Food Calories' in label:
                    data['food_calories'] = int(value.replace(',', ''))
                elif 'Exercise Calories' in label:
                    data['exercise_calories'] = int(value.replace(',', ''))
                elif 'Net Calories' in label:
                    data['net_calories'] = int(value.replace(',', ''))
                elif '+/- Calories' in label:
                    data['deficit'] = int(value.replace(',', '').replace('+', ''))
                elif 'Weight' in label and value != '-':
                    try:
                        data['weight'] = float(value)
                    except:
                        pass
    
    # Parse meals
    current_meal = None
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 3:
            first_cell = cells[0].get_text(strip=True)
            
            # Check if this is a meal header
            if first_cell in ['Breakfast', 'Lunch', 'Dinner', 'Snacks']:
                current_meal = {
                    'name': first_cell,
                    'calories': int(cells[-1].get_text(strip=True).replace(',', '')),
                    'items': []
                }
                data['meals'].append(current_meal)
            elif current_meal and first_cell and not first_cell.startswith('Nutrient'):
                # This is a food item
                item = {
                    'name': first_cell,
                    'serving': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                    'calories': int(cells[-1].get_text(strip=True).replace(',', ''))
                }
                current_meal['items'].append(item)
    
    return data


def format_for_checkin(data):
    """Format parsed data for morning check-in"""
    
    lines = ["📊 Yesterday's Nutrition (Lose It!)"]
    
    if data['food_calories']:
        lines.append(f"• Calories: {data['food_calories']:,} eaten")
        if data['exercise_calories']:
            lines.append(f"• Exercise: {data['exercise_calories']:,} burned")
        if data['net_calories']:
            lines.append(f"• Net: {data['net_calories']:,}")
    
    if data['deficit'] is not None:
        status = "✅" if data['deficit'] < 0 else "⚠️"
        lines.append(f"• Deficit: {data['deficit']:,} cal {status}")
    
    if data['weight']:
        lines.append(f"• Weight: {data['weight']} lbs")
    else:
        lines.append(f"• Weight: Not logged")
    
    # Meal summary
    if data['meals']:
        lines.append("")
        lines.append("Meals:")
        for meal in data['meals'][:3]:  # Top 3 meals
            lines.append(f"  • {meal['name']}: {meal['calories']} cal")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test with sample data
    test_html = """
    <h3>Daily Report for April 5, 2026</h3>
    <table>
    <tr><td>Food Calories</td><td>1,813</td></tr>
    <tr><td>Exercise Calories</td><td>97</td></tr>
    <tr><td>Net Calories</td><td>1,716</td></tr>
    <tr><td>+/- Calories</td><td>-134</td></tr>
    <tr><td>Weight</td><td>-</td></tr>
    </table>
    """
    
    data = parse_loseit_email(test_html, "Daily Report for April 5, 2026")
    print("Parsed data:")
    print(data)
    print("\nFormatted:")
    print(format_for_checkin(data))