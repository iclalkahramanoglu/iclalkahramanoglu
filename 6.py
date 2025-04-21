sozcuk= input("Bir sözcük giriniz: ")
sayi= int(input("Bir sayı giriniz: "))
harf= input("Bir harf giriniz: ")

degistirilmis= sozcuk[:sayi - 1] + harf + sozcuk[sayi:]
print degistirilmis