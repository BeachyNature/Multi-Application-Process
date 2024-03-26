# Define the list of strings
list_of_strings = ['index > 3', 'Index < 5']

# Word to check
word_to_check = 'index'

# Join the list into a single string separated by a space
combined_string = ' '.join(list_of_strings)

# Count occurrences of the word in the combined string
count = combined_string.lower().count(word_to_check.lower())

print(f"The word '{word_to_check}' appears {count} times in the list.")
