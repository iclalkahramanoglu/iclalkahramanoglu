cumle = input("Bir kelime veya cümle giriniz: ")
sil = input("Silinicek kelime? ")

kelime=""
yeni_cumle=""

i=0
while i < len(cumle):
  if cumle[i] != " ":
    kelime += cumle[i]
  else:
      if kelime != sil:
        yeni_cumle += kelime
print("Yeni cumle: "+ yeni_cumle)