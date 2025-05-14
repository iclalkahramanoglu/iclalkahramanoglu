import os
import time
import requests
import psycopg2
import tkinter as tk
from io import BytesIO
from PIL import Image, ImageTk
from bs4 import BeautifulSoup
from tkcalendar import Calendar
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from tkinter import ttk, messagebox, Toplevel, StringVar

# --- PostgreSQL bağlantısı (DBeaver ile oluşturduğunuz kullanıcı/DB'yi girin) ---
DB_PARAMS = dict(
    dbname="otelveri",
    user="otel_user",
    password="otel_pass123",
    host="localhost",
    port="5432"
)

IMAGE_FOLDER = "otel_resimleri"

# --- Tüm bölgeler ve iller (örnek için kısaltıldı, tamamını ekleyebilirsiniz) ---
regions_and_cities = {
    'Marmara': [
        'Edirne', 'Kırklareli', 'Tekirdağ', 'İstanbul', 'Kocaeli',
        'Sakarya', 'Yalova', 'Bilecik', 'Bursa', 'Balıkesir', 'Çanakkale'
    ],
    'Ege': [
        'İzmir', 'Aydın', 'Muğla', 'Denizli', 'Manisa',
        'Uşak', 'Kütahya', 'Afyonkarahisar'
    ],
    'Akdeniz': [
        'Antalya', 'Mersin', 'Adana', 'Osmaniye', 'Hatay',
        'Kahramanmaraş', 'Isparta', 'Burdur'
    ],
    'Karadeniz': [
        'Zonguldak', 'Bartın', 'Karabük', 'Sinop', 'Samsun',
        'Ordu', 'Giresun', 'Trabzon', 'Rize', 'Artvin',
        'Gümüşhane', 'Bayburt', 'Amasya', 'Çorum', 'Tokat',
        'Kastamonu', 'Bolu', 'Düzce'
    ],
    'İç Anadolu': [
        'Ankara', 'Konya', 'Kayseri', 'Eskişehir', 'Kırıkkale',
        'Kırşehir', 'Niğde', 'Nevşehir', 'Aksaray', 'Yozgat',
        'Sivas', 'Karaman'
    ],
    'Doğu Anadolu': [
        'Erzurum', 'Erzincan', 'Bayburt', 'Gümüşhane', 'Malatya',
        'Elazığ', 'Tunceli', 'Bingöl', 'Muş', 'Bitlis',
        'Van', 'Ağrı', 'Kars', 'Ardahan', 'Iğdır'
    ],
    'Güneydoğu Anadolu': [
        'Gaziantep', 'Şanlıurfa', 'Diyarbakır', 'Adıyaman', 'Mardin',
        'Şırnak', 'Siirt', 'Batman', 'Kilis'
    ]
}

def clear_images_folder():
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    for f in os.listdir(IMAGE_FOLDER):
        path = os.path.join(IMAGE_FOLDER, f)
        if os.path.isfile(path):
            os.unlink(path)

def load_image(url: str, name: str) -> ImageTk.PhotoImage:
    resp = requests.get(url)
    img = Image.open(BytesIO(resp.content))
    path = os.path.join(IMAGE_FOLDER, name)
    img.save(path)
    return ImageTk.PhotoImage(img)

def get_hotels(city, check_in, check_out, status_label):
    url = f'https://www.etstur.com/{city}-Otelleri?check_in={check_in}&check_out={check_out}&adult_1=1&child_1=0'
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        time.sleep(5)
        wait = WebDriverWait(driver, 15)
        status_label.config(text="Sonuçlar aranıyor...", fg="blue")
        while True:
            try:
                btn = driver.find_element(By.XPATH, '//*[@id="load-more-btn-area"]/button')
                btn.click()
                time.sleep(2)
                wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="load-more-btn-area"]/button')))
            except StaleElementReferenceException:
                continue
            except:
                break
        status_label.config(text="Sonuçlar hazır", fg="green")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.select("div.hotel-card-title")
        prices = soup.select("div.ets-section.hotel-card-wrapper p.amount")
        images = soup.select("div.slick-slide.slick-current.slick-active img")
        locs   = soup.select("div.hotel-card-location-comments p.location-wrap")
        rates  = soup.select("div.hotel-card-location-comments p.comment-wrap")

        results = []
        for i, title in enumerate(cards):
            name = title.get_text(strip=True)
            price = prices[i].get_text(strip=True) if i<len(prices) else "–"
            img_url = images[i]['src'] if i<len(images) else None
            loc  = locs[i].get_text(strip=True) if i<len(locs) else "–"
            rat  = rates[i].get_text(strip=True) if i<len(rates) else "–"
            results.append(dict(hotel_name=name, amount_price=price,
                                image_url=img_url, location=loc, rate=rat))
        return results

    finally:
        driver.quit()

def search_hotels(status_label, result_tree, city_cb, check_in_var, check_out_var):
    city = city_cb.get()
    ci   = check_in_var.get()
    co   = check_out_var.get()
    if not city or not ci or not co:
        messagebox.showwarning("Eksik", "Lütfen şehir, giriş ve çıkış tarihlerini seçin.")
        return
    clear_images_folder()
    hotels = get_hotels(city, ci, co, status_label)
    result_tree.delete(*result_tree.get_children())
    images = []
    for idx, h in enumerate(hotels,1):
        img = load_image(h['image_url'], f"otel_{idx}.png") if h['image_url'] else None
        images.append(img)
        result_tree.insert('', 'end',
            values=[idx, h['hotel_name'], h['amount_price'], h['location'], h['rate']],
            image=img)

def show_login_window():
    def on_login():
        un = user_var.get()
        pw = pass_var.get()
        try:
            conn = psycopg2.connect(**DB_PARAMS)
        except Exception as e:
            messagebox.showerror("DB Hatası", str(e))
            return
        cur = conn.cursor()
        cur.execute("SELECT * FROM users1 WHERE name=%s AND password=%s", (un,pw))
        if cur.fetchone():
            login_root.destroy()
            show_main_window()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre hatalı")

    def on_signup():
        sw = Toplevel(login_root)
        sw.title("Kayıt Ol")
        sw.geometry("300x200")
        Labels = ["Kullanıcı Adı","Şifre","E-posta","Ad","Soyad"]
        vars   = [StringVar() for _ in Labels]
        for i, txt in enumerate(Labels):
            tk.Label(sw, text=txt+":").grid(row=i, column=0,padx=5,pady=5,sticky="e")
            tk.Entry(sw,textvariable=vars[i], show="*" if i==1 else "").grid(row=i, column=1)
        def do_signup():
            vals = [v.get() for v in vars]
            cur = psycopg2.connect(**DB_PARAMS).cursor()
            cur.execute("INSERT INTO users1(name,password,email,first_name,last_name) VALUES(%s,%s,%s,%s,%s)", vals)
            cur.connection.commit()
            messagebox.showinfo("Tamam","Kayıt başarılı")
            sw.destroy()
        tk.Button(sw,text="Kayıt Ol", command=do_signup).grid(row=len(Labels),column=0,columnspan=2,pady=10)

    global login_root, user_var, pass_var
    login_root = tk.Tk()
    login_root.title("User Login")
    login_root.geometry("300x150")
    user_var = StringVar()
    pass_var = StringVar()
    tk.Label(login_root, text="Username:").grid(row=0,column=0,padx=5,pady=5,sticky="e")
    tk.Entry(login_root,textvariable=user_var).grid(row=0,column=1)
    tk.Label(login_root, text="Password:").grid(row=1,column=0,padx=5,pady=5,sticky="e")
    tk.Entry(login_root,textvariable=pass_var, show="*").grid(row=1,column=1)
    tk.Button(login_root, text="Login",   width=10, command=on_login).grid(row=2,column=0,pady=10)
    tk.Button(login_root, text="Sign Up", width=10, command=on_signup).grid(row=2,column=1,pady=10)
    login_root.mainloop()

def show_main_window():
    root = tk.Tk()
    root.title("Otel Arama")
    root.geometry("800x600")

    # Bölge / Şehir / Tarih seçimleri
    tk.Label(root, text="Bölge:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    region_cb = ttk.Combobox(root, values=list(regions_and_cities.keys()), state="readonly")
    region_cb.grid(row=0, column=1, padx=5, pady=5)
    tk.Label(root, text="Şehir:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    city_cb   = ttk.Combobox(root, values=[], state="readonly")
    city_cb.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(root, text="Giriş:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    ci_var = StringVar()
    tk.Entry(root, textvariable=ci_var, state="readonly").grid(row=0, column=3)
    tk.Button(root, text="Takvim", command=lambda: open_calendar(ci_var)).grid(row=0,column=4)

    tk.Label(root, text="Çıkış:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
    co_var = StringVar()
    tk.Entry(root, textvariable=co_var, state="readonly").grid(row=1, column=3)
    tk.Button(root, text="Takvim", command=lambda: open_calendar(co_var)).grid(row=1,column=4)

    tk.Button(root, text="Ara", command=lambda: search_hotels(
        status_label, result_tree, city_cb, ci_var, co_var
    )).grid(row=2, column=0, columnspan=5, pady=10)

    status_label = tk.Label(root, text="", fg="black")
    status_label.grid(row=3, column=0, columnspan=5)

    # Otel sonuçları tablosu
    cols = ('#','Ad','Fiyat','Konum','Puan')
    result_tree = ttk.Treeview(root, columns=cols, show='headings', height=15)
    for c,w in zip(cols,[30,200,100,200,80]):
        result_tree.heading(c, text=c); result_tree.column(c, width=w)
    result_tree.grid(row=4, column=0, columnspan=5, padx=5, pady=5)

    # Bölge seçilince şehirleri güncelle
    def on_region(evt):
        city_cb['values'] = regions_and_cities.get(region_cb.get(), [])
        city_cb.set('')
    region_cb.bind("<<ComboboxSelected>>", on_region)

    root.mainloop()

if _name_ == '_main_':
    show_login_window()