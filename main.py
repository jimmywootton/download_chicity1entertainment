from funcs import *

channel_url = 'https://www.youtube.com/ChiCity1Entertainment'
urls = get('webpage_url', channel_url).split('\n')[:-1]
urls.reverse()

with open('placeholder.txt', 'r') as file:
    init_array = int(file.read())

for i in range(init_array, len(urls)):
    for j in range(5):
        try:
            driver(urls[i])
            with open("placeholder.txt", "w") as file:
                file.write(str(i))
            break
        except Exception:
            print(f'Number {j} retry on {urls[i]}')
    else:
        sys.exit('Exit')