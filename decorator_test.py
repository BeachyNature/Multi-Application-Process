class Pizza(object):
    def __init__(self):
        self.toppings = []

    def __call__(self, topping):
        # When using '@instance_of_pizza' before a function definition
        # the function gets passed onto 'topping'.
        self.toppings.append(topping())

    def __repr__(self):
        return str(self.toppings)

pizza = Pizza()

@pizza
def cheese():
    return 'cheese'
@pizza
def sauce():
    return 'sauce'

print(f"{pizza = }")

# Anon Func test
lam_test = (lambda x, y: x+y)

epic = lam_test(1, 2)
print(f"{epic = }")

# Decorator test
def test(func):
    def wrapper():
        func()
        print(func.__name__)
    return wrapper

@test
def run_this():
    print("THIS IS SICK")

run_this()


# Run one line at time, good for memory
def run_file(filename):
    with open(filename, 'r') as file:
        for line in file:
            yield line

zen = run_file('/Users/tycon/Desktop/Test CSVS/organizations-500000.csv')
print(next(zen))
print(next(zen))


# Walrus test
import time
 
def count_odds(numbers):
    time.sleep(1)
    odds = [o for o in numbers if o%2 == 1]
    return len(odds)

numbers = [1, 2, 3, 4, 5]

if (n:= count_odds(numbers)) > 1:
    print(f"{n = }")


epic = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

for i in epic:
    if (nice:=i) > 5:
        print(f"{nice = }")