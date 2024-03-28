import polars as pl
import re

# Sample DataFrame creation (you should replace this with your actual DataFrame)
data = {'index': [11, 6, 3, 8, 12], 'city': ['Rayville', 'New York', 'Chicago', 'Rayville', 'Los Angeles']}
df = pl.DataFrame(data)

input_string = 'city = Rayville or city = Chicago, index < 6 or index > 10'

# Define regular expression patterns for splitting
pattern_condition = r'\s*([^\s=><]+)\s*([=><])\s*([^\s=><]+)\s*'

# Initialize an empty filter expression
combined_filter = None

# Split the input string into individual conditions
condition_sets = input_string.split(',')

# Process each set of conditions
for condition_set in condition_sets:
    # Extract conditions from the input string
    matches = re.findall(pattern_condition, condition_set)
    
    # Initialize an empty filter expression for each set of conditions
    condition_filter_set = None
    
    # Process each condition in the set
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
                case _ :
                    print(f"Invalid operator: {operator}")
        else:
            filter_expr = pl.col(column) == value
        
        # Combine filter expressions for the current condition set using logical OR
        if condition_filter_set is None:
            condition_filter_set = filter_expr
        else:
            condition_filter_set = condition_filter_set | filter_expr
        
# Combine filter expressions for each set of conditions using logical AND
if combined_filter is None:
    combined_filter = condition_filter_set
else:
    combined_filter = combined_filter & condition_filter_set


df = df.filter(combined_filter)

# Display the filtered DataFrame
print(df)
