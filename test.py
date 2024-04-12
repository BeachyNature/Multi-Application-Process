import itertools
import polars as pl
import re

def index_row(df, columns, data_dict):
    rows = df['index'].to_list()
    for row, col in itertools.product(rows, columns):
        if row in data_dict:
            data_dict[row].append(col)
        else:
            data_dict[row] = [col]
    return data_dict

columns = []
or_expr = []
data_dict = {}
combined_filter = None

input_string = "index < 10 or (index > 5 and city = Rayville)"
df = pl.DataFrame({'index': [11, 6, 3, 8, 12, 2], 'city': ['Rayville', 'New York', 'Chicago', 'Rayville', 'LosAngeles', 'Rayville']})

# TEST --------------------------
# final_df = pl.col('index') < 10 | (pl.col('index') > 5 & (pl.col('city') == 'Rayville'))
# epic = df.filter(final_df)
# print(f"{epic = }")

# Split the input string into individual conditions
condition_sets = re.split(r'(?:and|&|,)', input_string)

# Define regular expression patterns for splitting
pattern_condition = r'\s*([^\s=><!]+)\s*([=><!]+)\s*([^\s=><!]+)\s*'


# Process each condition set
for val in condition_sets:
    matches = re.findall(pattern_condition, val)

    for match in matches:
        column = re.sub(r"\(|\)", "", match[0].strip())
        operator = re.sub(r"\(|\)", "", match[1].strip())
        value = re.sub(r"\(|\)", "", match[2].strip())

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
        columns.append(column)
        or_expr.append(filter_expr)

#         # Combine filter expressions based on 'and' or 'or' logic
#         if 'or' in val:
#             combined_filter = filter_expr if combined_filter is None else combined_filter | filter_expr
#         else:
#             combined_filter = filter_expr if combined_filter is None else combined_filter & filter_expr

# df = df.filter(combined_filter)
# data_dict = index_row(df, columns, data_dict)


if "(" in input_string:
    for i in or_expr:
        df = df.filter(i)
        data_dict = index_row(df, columns, data_dict)

        print(f"{df = }")
        print(f"{data_dict = }")
        
print("EPIC -----------------")
print(f"{df = }")
print(f"{data_dict = }")

for key, value in (
    itertools.chain.from_iterable(
        (itertools.product((k,), v) for k, v in data_dict.items()))):
            print(key)
            print(value)

# print(f"{str(combined_filter) = }")

# # Display the filtered DataFrame
# if combined_filter is not None:
#     df = df.filter(combined_filter)
# print(f"{df = }")


