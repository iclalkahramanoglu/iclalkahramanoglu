kelime= input("Bir kelime giriniz: ")
sayi= int(input("Sayı Giriniz: "))

if sayi > len(kelime):
  print("hata")
  
else:
  ilk = kelime[:sayi]
  son = kelime[sayi:]
  
  print(ilk +"-"+ son)