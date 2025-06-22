import csv

def parse_presentations(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    presentations = content.split('---\n')
    parsed_data = []
    
    for presentation in presentations:
        if not presentation.strip():
            continue
            
        data = {}
        lines = presentation.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                data[key] = value
        
        parsed_data.append(data)
    
    return parsed_data

def write_to_csv(data, output_file):
    if not data:
        return
        
    fieldnames = data[0].keys()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Uso del código
input_file = 'presentations_extracted.txt'
output_file = 'presentations.csv'

presentations_data = parse_presentations(input_file)
write_to_csv(presentations_data, output_file)

print(f"Se ha generado el archivo CSV: {output_file}")
