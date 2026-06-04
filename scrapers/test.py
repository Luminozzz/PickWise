from rapidfuzz import fuzz

def test(actual, test):
    return print(word.lower() in test for word in test)

if __name__ == "__main__":
    print(test(['g502', 'lightspeed'], ['Logitech', 'G502', 'Lightspeed', 'Wireless', 'Gaming', 'Mouse']))