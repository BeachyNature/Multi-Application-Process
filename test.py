import re
import itertools
import polars as pl


"""
Get the index row and column values for highlighting
"""
def index_row(df, columns, data_dict) -> dict:
    rows = df['index'].to_list()
    for row in rows:
        if row in data_dict:
            data_dict[row].append(columns)
        else:
            data_dict[row] = [columns]
    return data_dict


"""
Dynamically setup the expressions
"""
def dynamic_expr(operator, value, column, filter_expr) -> filter:
    if value.isdigit():
        match operator:
            case '=':
                filter_expr = pl.col(column) == int(value)
            case '>':
                filter_expr = pl.col(column) > int(value)
            case '<':
                filter_expr = pl.col(column) < int(value)
            case '>=':
                filter_expr = pl.col(column) >= int(value)
            case '<=':
                filter_expr = pl.col(column) <= int(value)
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
    return filter_expr


"""
Process dataframe and index rows
"""
def process_filter(df, col, data_dict, combined_filter):
    df = df.filter(combined_filter)
    data_dict = index_row(df, col, data_dict)
    return data_dict


"""
Split the conditions up into sets and combine back together
"""
def condition_set(init_val, df, condition, pattern,
                combined_filter, data_dict, _bool) -> dict:
    print("NICE", condition)

    for cond_set in condition:
        matches = re.findall(pattern, cond_set)
        for match in matches:
            col = re.sub(r"\(|\)", "", match[0].strip())
            op = re.sub(r"\(|\)", "", match[1].strip())
            val = re.sub(r"\(|\)", "", match[2].strip())
        filter_expr = dynamic_expr(op, val, col, None)

        if _bool:
            combined_filter = filter_expr if combined_filter is None else combined_filter | filter_expr
        else:
            combined_filter = filter_expr if combined_filter is None else combined_filter & filter_expr

        if re.search(r'[()]', init_val) is not None:
            data_dict = process_filter(df, col, data_dict, combined_filter)

    data_dict = process_filter(df, col, data_dict, combined_filter)
    return data_dict


"""
Detect whether the condition is split between and/or condition or none
"""
def match_bool(val, data_dict, combined_filter) -> dict:
    # Dataframe setup
    df = pl.DataFrame({'index': [11, 6, 3, 8, 12, 2], 'city': ['Rayville', 'New York', 'Chicago', 'Rayville', 'LosAngeles', 'Rayville']})

    print(f"{val = }")
    pattern = r'\s*([^\s=><!]+)\s*([=><!]+)\s*([^\s=><!]+)\s*'

    if 'and' in val:
        print("NICE")
        condition = re.split(r'(?:and|&|,)', val)
        data_dict =  condition_set(val, df, condition, pattern,
                                combined_filter, data_dict, False)
        return data_dict

    elif 'or' in val:
        print("EPIC")
        condition = re.split(r'\bor\b', val)
        data_dict =  condition_set(val, df, condition, pattern,
                                combined_filter, data_dict, True)
        return data_dict
    else:
        print("COOL")
        col, op, val = map(str.strip, val.split())
        filter_expr = dynamic_expr(op, val, col, None)

    if filter_expr is not None:
        df = df.filter(filter_expr)
        data_dict = index_row(df, col, data_dict)
        return data_dict
    return


# TEST --------------------------
# final_df = pl.col('index') < 10 | (pl.col('index') > 5 & (pl.col('city') == 'Rayville'))
# epic = df.filter(final_df)

data_dict = {}
combined_filter = None

# input_string = "index = 11 and city = Rayville"
input_string = "index < 10 (index > 5 and city = Rayville)"

# Process each condition set
if re.search(r'[()]', input_string) is not None:
    # Find all matches of the pattern in the text
    value = re.findall(r'\((.*?)\)', input_string)

value = re.findall(r'\([^()]*\)|[^()]+', input_string)
print(f"{value = }")

for val in value:
    data_dict = match_bool(val, data_dict, combined_filter) 
    print(f"{data_dict = }")

for key, value in (
    itertools.chain.from_iterable(
        (itertools.product((k,), v) for k, v in data_dict.items()))):
            print(key)
            print(value)
