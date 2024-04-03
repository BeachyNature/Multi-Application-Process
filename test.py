import polars as pl
import re

data = {'index': [11, 6, 3, 8, 12], 'city': ['Rayville', 'New York', 'Chicago', 'Rayville', 'LosAngeles']}
df = pl.DataFrame(data)

input_string = input("Enter conditional: ")

# Define regular expression patterns for splitting
pattern_condition = r'\s*([^\s=><!]+)\s*([=><!]+)\s*([^\s=><!]+)\s*'

# Split the input string into individual conditions
condition_sets = re.split(r'(?:and|&|,)', input_string)

combined_filter = None

# Process each condition set
for val in condition_sets:
    matches = re.findall(pattern_condition, val)

    for match in matches:
        column = match[0].strip()
        operator = match[1].strip()
        value = match[2].strip()    
        
        # Build filter expression for the current condition
        if value.isdigit():
            match operator:
                case '=':
                    filter_expr = pl.col(column) == int(value)
                case '>':
                    filter_expr = pl.col(column) > int(value)
                case '<':
                    filter_expr = pl.col(column) < int(value)
                case '!=':
                    filter_expr = pl.col(column) != int(value)
                case _ :
                    print(f"Invalid operator: {operator}")
        else:
            match operator:
                case '=': 
                    filter_expr = pl.col(column) == value
                case '!=':
                    filter_expr = pl.col(column) != value
                case _ :
                    print(f"Invalid operator: {operator}")

        # Combine filter expressions based on 'and' or 'or' logic
        if 'or' in val:
            combined_filter = filter_expr if combined_filter is None else combined_filter | filter_expr
        else:
            combined_filter = filter_expr if combined_filter is None else combined_filter & filter_expr

print(f"{combined_filter = }")

# Display the filtered DataFrame
if combined_filter is not None:
    df = df.filter(combined_filter)
print(df)
