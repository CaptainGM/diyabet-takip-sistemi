import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk
import mysql.connector
import datetime
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from tkcalendar import DateEntry

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'diyabet_takip_sistemi')
}

main_window = None
current_user_id = None
current_user_ad = None
current_user_soyad = None
current_user_rol_adi = None
current_patient_id = None
current_user_doctor_id = None


def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Veritabanı Bağlantı Hatası", f"Veritabanına bağlanılamadı: {err}\n"
                                                     f"Lütfen MySQL sunucusunun çalıştığından ve '{DB_CONFIG['user']}' kullanıcısı için şifrenin doğru olduğundan emin olun.")
        return None

def clear_window(window):
    for widget in window.winfo_children():
        widget.destroy()

def show_login_screen():
    global current_user_id, current_user_ad, current_user_soyad, current_user_rol_adi, current_patient_id, current_user_doctor_id
    current_user_id = None
    current_user_ad = None
    current_user_soyad = None
    current_user_rol_adi = None
    current_patient_id = None
    current_user_doctor_id = None

    clear_window(main_window)
    main_window.title("Diyabet Takip Sistemi Giriş")
    main_window.geometry("400x250")

    tk.Label(main_window, text="T.C. Kimlik No:", font=("Arial", 12)).pack(pady=10)
    tc_kimlik_entry = tk.Entry(main_window, width=30)
    tc_kimlik_entry.pack()
    tc_kimlik_entry.focus_set()

    tk.Label(main_window, text="Şifre:", font=("Arial", 12)).pack(pady=10)
    password_entry = tk.Entry(main_window, show="*", width=30)
    password_entry.pack()

    login_button = tk.Button(main_window, text="Giriş Yap", command=lambda: login_user(tc_kimlik_entry, password_entry))
    login_button.pack(pady=20)

    main_window.bind('<Return>', lambda event: login_user(tc_kimlik_entry, password_entry))

def login_user(tc_kimlik_entry, password_entry):
    global current_user_id, current_user_ad, current_user_soyad, current_user_rol_adi, current_patient_id, current_user_doctor_id

    tc_no = tc_kimlik_entry.get().strip()
    password = password_entry.get().strip()

    if not tc_no or not password:
        messagebox.showwarning("Giriş Hatası", "T.C. Kimlik No ve Şifre boş bırakılamaz!")
        return

    if not tc_no.isdigit() or len(tc_no) != 11:
        messagebox.showerror("Giriş Hatası", "T.C. Kimlik No 11 haneli sayı olmalıdır!")
        return

    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor(buffered=True, dictionary=True)
    try:
        query = "SELECT kullanici_id, ad, soyad, sifre, rol_id FROM kullanicilar WHERE tc_kimlik_no = %s AND aktif_durum = TRUE"
        cursor.execute(query, (tc_no,))
        user_data = cursor.fetchone()

        if user_data:
            stored_password = user_data['sifre']
            if password == stored_password: 
                current_user_id = user_data['kullanici_id']
                current_user_ad = user_data['ad']
                current_user_soyad = user_data['soyad']
                
                cursor.execute("SELECT rol_adi FROM kullanici_rolleri WHERE rol_id = %s", (user_data['rol_id'],))
                rol_result = cursor.fetchone()
                if rol_result:
                    current_user_rol_adi = rol_result['rol_adi']

                    if current_user_rol_adi == "Hasta":
                        cursor.execute("SELECT hasta_id FROM hastalar WHERE kullanici_id = %s", (current_user_id,))
                        hasta_result = cursor.fetchone()
                        if hasta_result:
                            current_patient_id = hasta_result['hasta_id']
                        else:
                            messagebox.showerror("Giriş Başarısız", "Hasta kaydınız bulunamadı.")
                            return
                    elif current_user_rol_adi == "Doktor":
                        cursor.execute("SELECT doktor_id FROM doktorlar WHERE kullanici_id = %s", (current_user_id,))
                        doktor_result = cursor.fetchone()
                        if doktor_result:
                            current_user_doctor_id = doktor_result['doktor_id']
                        else:
                            messagebox.showerror("Giriş Başarısız", "Doktor kaydınız bulunamadı.")
                            return
                    
                    messagebox.showinfo("Giriş Başarılı", f"Hoş geldiniz, {current_user_ad} {current_user_soyad} ({current_user_rol_adi})!")
                    show_main_app_screen()
                else:
                    messagebox.showerror("Giriş Başarısız", "Kullanıcı rolü tanımlanamadı.")
            else:
                messagebox.showerror("Giriş Başarısız", "Yanlış T.C. Kimlik No veya Şifre.")
        else:
            messagebox.showerror("Giriş Başarısız", "Yanlış T.C. Kimlik No veya Şifre veya kullanıcı aktif değil.")

    except mysql.connector.Error as db_err:
        messagebox.showerror("Veritabanı Hatası", f"Veritabanı sorgu hatası: {db_err}")
    except Exception as e:
        messagebox.showerror("Sorgu Hatası", f"Giriş sırasında bir hata oluştu: {e}")
    finally:
        cursor.close()
        conn.close()

def show_main_app_screen():
    clear_window(main_window)
    main_window.title(f"Diyabet Takip Sistemi - {current_user_rol_adi}")
    main_window.geometry("1000x750")

    header_frame = tk.Frame(main_window, pady=10)
    header_frame.pack(fill="x")

    tk.Label(header_frame, text=f"Giriş Yapan: {current_user_ad} {current_user_soyad}",
             font=("Arial", 14, "bold")).pack(side="left", padx=20)
    tk.Label(header_frame, text=f"Rol: {current_user_rol_adi}",
             font=("Arial", 12)).pack(side="left", padx=20)

    tk.Button(header_frame, text="Çıkış Yap", command=show_login_screen,
              bg="red", fg="white", width=12, height=1).pack(side="right", padx=20)

    button_frame = tk.Frame(main_window, pady=20)
    button_frame.pack(expand=True)

    button_width = 45
    button_height = 2
    button_font = ("Arial", 11)

    if current_user_rol_adi == "Doktor":
        tk.Button(button_frame, text="Hastalarımı Görüntüle ve Filtrele",
                  command=lambda: show_doctor_patients_with_filters(main_window),
                  width=button_width, height=button_height, font=button_font).pack(pady=7)
        tk.Button(button_frame, text="Yeni Hasta Ekle",
                  command=lambda: add_patient_screen(main_window),
                  width=button_width, height=button_height, font=button_font).pack(pady=7)
        tk.Button(button_frame, text="Hasta Uyarılarını Görüntüle",
                  command=lambda: show_doctor_alerts(main_window),
                  width=button_width, height=button_height, font=button_font).pack(pady=7)
        tk.Button(button_frame, text="Kritik Hastaları Görüntüle",
                  command=lambda: show_critical_patients(main_window),
                  width=button_width, height=button_height, font=button_font).pack(pady=7)
        tk.Button(button_frame, text="Hasta Raporu Oluştur",
                  command=lambda: show_patient_report_options(main_window),
                  width=button_width, height=button_height, font=button_font).pack(pady=7)
        tk.Button(button_frame, text="Hastaya Plan/Belirti Ata",
                  command=lambda: show_add_to_system_options(main_window),
                  width=button_width, height=button_height, font=button_font).pack(pady=7)

    elif current_user_rol_adi == "Hasta":
        tk.Button(button_frame, text="Kan Şekeri Ölçümü Gir",
                  command=lambda: enter_blood_sugar(main_window, current_user_id),
                  width=button_width, height=button_height, font=button_font).pack(pady=5)
        tk.Button(button_frame, text="Diyet/Egzersiz Durumu Gir",
                  command=lambda: enter_diet_exercise(main_window, current_user_id),
                  width=button_width, height=button_height, font=button_font).pack(pady=5)
        tk.Button(button_frame, text="Semptom Takibi Yap",
                  command=lambda: enter_symptoms(main_window, current_user_id),
                  width=button_width, height=button_height, font=button_font).pack(pady=5)
        tk.Button(button_frame, text="Kan Şekeri Geçmişi, Ort. ve Grafikler",
                  command=lambda: show_blood_sugar_history_and_graphs(main_window, current_user_id),
                  width=button_width, height=button_height, font=button_font).pack(pady=5)
        tk.Button(button_frame, text="Diyet/Egzersiz Uyum Takibi (%)",
                  command=lambda: show_patient_compliance(main_window, current_user_id),
                  width=button_width, height=button_height, font=button_font).pack(pady=5)
        tk.Button(button_frame, text="İnsülin Önerilerim (Filtreli)",
                  command=lambda: show_insulin_recommendations_for_patient_filtered(main_window, current_user_id),
                  width=button_width, height=button_height, font=button_font).pack(pady=5)
        tk.Button(button_frame, text="Bildirimlerim",
                  command=lambda: show_patient_notifications(main_window, current_user_id),
                  width=button_width, height=button_height, font=button_font).pack(pady=5)
        tk.Button(button_frame, text="Doktorumun Planları ve Notları",
                  command=lambda: show_doctor_plans_for_patient(main_window),
                  width=button_width, height=button_height, font=button_font).pack(pady=5)
    else:
        tk.Label(button_frame, text=f"Bilinmeyen rol: {current_user_rol_adi}",
                 font=("Arial", 12), fg="red").pack(pady=20)

def show_doctor_plans_for_patient(parent_window):
    plans_window = tk.Toplevel(parent_window)
    plans_window.title("Doktorumun Planları ve Notları")
    plans_window.geometry("800x600")

    tk.Label(plans_window, text="Doktorunuz Tarafından Atanan Aktif Planlar ve Notlar", font=("Arial", 14, "bold")).pack(pady=10)

    notebook = ttk.Notebook(plans_window)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    diet_plan_frame = tk.Frame(notebook)
    notebook.add(diet_plan_frame, text="Aktif Diyet Planım")
    load_active_diet_plan_for_patient(diet_plan_frame)

    exercise_plan_frame = tk.Frame(notebook)
    notebook.add(exercise_plan_frame, text="Aktif Egzersiz Planım")
    load_active_exercise_plan_for_patient(exercise_plan_frame)

    symptoms_frame = tk.Frame(notebook)
    notebook.add(symptoms_frame, text="Doktor Tarafından Girilen Son Belirtilerim")
    load_doctor_recorded_symptoms_for_patient(symptoms_frame)
    
    doctor_notes_frame = tk.Frame(notebook)
    notebook.add(doctor_notes_frame, text="Doktorumun Notları (Paylaşılan)")
    load_shared_doctor_notes_for_patient(doctor_notes_frame)


def load_active_diet_plan_for_patient(parent_frame):
    for widget in parent_frame.winfo_children(): widget.destroy()
    conn = connect_db()
    if not conn: 
        tk.Label(parent_frame, text="Veritabanı bağlantı hatası.").pack(padx=10, pady=20)
        return
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT dt.diyet_adi, dt.aciklama as diyet_aciklama, dp.baslangic_tarihi, dp.bitis_tarihi
            FROM diyet_planlari dp
            JOIN diyet_turleri dt ON dp.diyet_turu_id = dt.diyet_turu_id
            WHERE dp.hasta_id = %s AND dp.aktif_durum = TRUE 
            AND dp.baslangic_tarihi <= CURDATE() 
            AND (dp.bitis_tarihi IS NULL OR dp.bitis_tarihi >= CURDATE())
            ORDER BY dp.olusturma_tarihi DESC LIMIT 1
        """, (current_patient_id,))
        plan = cursor.fetchone()
        if plan:
            tk.Label(parent_frame, text=f"Diyet Adı: {plan['diyet_adi']}", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            tk.Label(parent_frame, text=f"Açıklama: {plan['diyet_aciklama']}", wraplength=700, justify=tk.LEFT).pack(anchor="w", padx=10, pady=2)
            tk.Label(parent_frame, text=f"Başlangıç: {plan['baslangic_tarihi'].strftime('%d.%m.%Y')}", font=("Arial", 10)).pack(anchor="w", padx=10, pady=2)
            if plan['bitis_tarihi']:
                tk.Label(parent_frame, text=f"Bitiş: {plan['bitis_tarihi'].strftime('%d.%m.%Y')}", font=("Arial", 10)).pack(anchor="w", padx=10, pady=2)
            else:
                tk.Label(parent_frame, text="Bitiş: Devam Ediyor", font=("Arial", 10)).pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(parent_frame, text="Şu anda size atanmış aktif bir diyet planı bulunmamaktadır.").pack(padx=10, pady=20)
    except Exception as e:
        tk.Label(parent_frame, text=f"Diyet planı yüklenirken hata: {e}").pack(padx=10, pady=20)
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def load_active_exercise_plan_for_patient(parent_frame):
    for widget in parent_frame.winfo_children(): widget.destroy()
    conn = connect_db()
    if not conn: 
        tk.Label(parent_frame, text="Veritabanı bağlantı hatası.").pack(padx=10, pady=20)
        return
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT et.egzersiz_adi, et.aciklama as egzersiz_aciklama, ep.baslangic_tarihi, ep.bitis_tarihi, ep.haftalik_siklik, ep.sure_dakika
            FROM egzersiz_planlari ep
            JOIN egzersiz_turleri et ON ep.egzersiz_turu_id = et.egzersiz_turu_id
            WHERE ep.hasta_id = %s AND ep.aktif_durum = TRUE
            AND ep.baslangic_tarihi <= CURDATE() 
            AND (ep.bitis_tarihi IS NULL OR ep.bitis_tarihi >= CURDATE())
            ORDER BY ep.olusturma_tarihi DESC LIMIT 1
        """, (current_patient_id,))
        plan = cursor.fetchone()
        if plan:
            tk.Label(parent_frame, text=f"Egzersiz Adı: {plan['egzersiz_adi']}", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            tk.Label(parent_frame, text=f"Açıklama: {plan['egzersiz_aciklama']}", wraplength=700, justify=tk.LEFT).pack(anchor="w", padx=10, pady=2)
            tk.Label(parent_frame, text=f"Sıklık: Haftada {plan['haftalik_siklik']} gün, {plan['sure_dakika']} dakika", font=("Arial", 10)).pack(anchor="w", padx=10, pady=2)
            tk.Label(parent_frame, text=f"Başlangıç: {plan['baslangic_tarihi'].strftime('%d.%m.%Y')}", font=("Arial", 10)).pack(anchor="w", padx=10, pady=2)
            if plan['bitis_tarihi']:
                tk.Label(parent_frame, text=f"Bitiş: {plan['bitis_tarihi'].strftime('%d.%m.%Y')}", font=("Arial", 10)).pack(anchor="w", padx=10, pady=2)
            else:
                tk.Label(parent_frame, text="Bitiş: Devam Ediyor", font=("Arial", 10)).pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(parent_frame, text="Size atanmış aktif bir egzersiz planı bulunmamaktadır.").pack(padx=10, pady=20)
    except Exception as e:
        tk.Label(parent_frame, text=f"Egzersiz planı yüklenirken hata: {e}").pack(padx=10, pady=20)
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def load_doctor_recorded_symptoms_for_patient(parent_frame):
    for widget in parent_frame.winfo_children(): widget.destroy()
    text_area = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=75, height=10, font=("Arial", 10))
    text_area.pack(padx=10, pady=10, fill="both", expand=True)
    text_area.insert(tk.END, "Doktorunuz Tarafından Kaydedilen Son Belirtiler (Son 7 Gün):\n\n")
    
    conn = connect_db()
    if not conn: 
        text_area.insert(tk.END, "Veritabanı bağlantı hatası.")
        text_area.config(state=tk.DISABLED)
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.belirti_adi, hb.siddet_seviyesi, hb.notlar as doktor_notu, hb.kayit_tarihi
            FROM hasta_belirtileri hb
            JOIN belirtiler b ON hb.belirti_id = b.belirti_id
            WHERE hb.hasta_id = %s AND hb.doktor_id IS NOT NULL 
            AND hb.kayit_tarihi >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            ORDER BY hb.kayit_tarihi DESC, hb.kayit_zamani DESC
        """, (current_patient_id,))
        symptoms = cursor.fetchall()
        if symptoms:
            for s in symptoms:
                text_area.insert(tk.END, f"Tarih: {s['kayit_tarihi'].strftime('%d.%m.%Y')}\n")
                text_area.insert(tk.END, f"  Belirti: {s['belirti_adi']}\n")
                if s['siddet_seviyesi']:
                    text_area.insert(tk.END, f"  Şiddet: {s['siddet_seviyesi']}\n")
                if s['doktor_notu']:
                    text_area.insert(tk.END, f"  Doktor Notu: {s['doktor_notu']}\n")
                text_area.insert(tk.END, "---\n")
        else:
            text_area.insert(tk.END, "Doktorunuz tarafından son 7 günde kaydedilmiş belirti bulunmamaktadır.")
    except Exception as e:
        text_area.insert(tk.END, f"Belirtiler yüklenirken hata: {e}")
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
    text_area.config(state=tk.DISABLED)

def load_shared_doctor_notes_for_patient(parent_frame):
    for widget in parent_frame.winfo_children(): widget.destroy()
    text_area = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=75, height=10, font=("Arial", 10))
    text_area.pack(padx=10, pady=10, fill="both", expand=True)
    text_area.insert(tk.END, "Doktorunuzun Sizinle Paylaştığı Notlar:\n\n")
    
    conn = connect_db()
    if not conn:
        text_area.insert(tk.END, "Veritabanı bağlantı hatası.")
        text_area.config(state=tk.DISABLED)
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT not_basligi, not_icerigi, olusturma_tarihi, onem_seviyesi
            FROM doktor_hasta_notlari
            WHERE hasta_id = %s AND gorunurluk = 'Doktor ve Hasta'
            ORDER BY olusturma_tarihi DESC
        """, (current_patient_id,))
        notes = cursor.fetchall()
        if notes:
            for note in notes:
                text_area.insert(tk.END, f"Tarih: {note['olusturma_tarihi'].strftime('%d.%m.%Y %H:%M')}\n")
                text_area.insert(tk.END, f"Başlık: {note['not_basligi']} (Önem: {note['onem_seviyesi']})\n")
                text_area.insert(tk.END, f"İçerik: {note['not_icerigi']}\n")
                text_area.insert(tk.END, "-----------------------------------\n\n")
        else:
            text_area.insert(tk.END, "Doktorunuzun sizinle paylaştığı bir not bulunmamaktadır.")
    except Exception as e:
        text_area.insert(tk.END, f"Doktor notları yüklenirken hata: {e}")
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
    text_area.config(state=tk.DISABLED)

def show_add_to_system_options(parent_window):
    clear_window(parent_window)
    parent_window.title("Doktor: Hastaya Plan/Belirti Ata")
    parent_window.geometry("600x500")

    main_frame = tk.Frame(parent_window, padx=20, pady=20)
    main_frame.pack(expand=True, fill="both")

    title_label = tk.Label(main_frame, text="İşlem Türünü Seçin", font=("Arial", 18, "bold"))
    title_label.pack(pady=20)

    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=20)

    tk.Button(button_frame, text="Hastaya Belirti Kaydı Yap",
              command=lambda: manage_symptoms_for_patient_by_doctor(parent_window),
              width=40, height=3, font=("Arial", 12)).pack(pady=10)
    tk.Button(button_frame, text="Hastaya Egzersiz Planı Ata",
              command=lambda: manage_exercise_recommendations(parent_window),
              width=40, height=3, font=("Arial", 12)).pack(pady=10)
    tk.Button(button_frame, text="Hastaya Beslenme Planı Ata",
              command=lambda: manage_diet_plans(parent_window),
              width=40, height=3, font=("Arial", 12)).pack(pady=10)

    tk.Button(main_frame, text="Ana Menüye Dön", command=lambda: show_main_app_screen(),
              width=20, height=2, font=("Arial", 10)).pack(pady=30)

def manage_symptoms_for_patient_by_doctor(parent_window):
    clear_window(parent_window)
    parent_window.title("Doktor: Hastaya Belirti Kaydı Yap")
    parent_window.geometry("600x650")

    main_frame = tk.Frame(parent_window, padx=20, pady=20)
    main_frame.pack(expand=True, fill="both")

    tk.Label(main_frame, text="Hastaya Belirti Ata", font=("Arial", 16, "bold")).pack(pady=10)

    tk.Label(main_frame, text="Hastanın T.C. Kimlik Numarası:", font=("Arial", 12)).pack(pady=5)
    patient_tc_entry = tk.Entry(main_frame, width=30)
    patient_tc_entry.pack(pady=5)
    patient_tc_entry.focus_set()

    symptoms_options = get_symptom_options() 
    symptom_vars = {}

    symptoms_scroll_frame = tk.Frame(main_frame, relief="sunken", borderwidth=1)
    symptoms_scroll_frame.pack(pady=10, fill="x", expand=True)
    symptoms_canvas = tk.Canvas(symptoms_scroll_frame, height=150)
    symptoms_scrollbar = tk.Scrollbar(symptoms_scroll_frame, orient="vertical", command=symptoms_canvas.yview)
    symptoms_inner_frame = tk.Frame(symptoms_canvas)
    symptoms_inner_frame.bind("<Configure>", lambda e: symptoms_canvas.configure(scrollregion=symptoms_canvas.bbox("all")))
    symptoms_canvas.create_window((0,0), window=symptoms_inner_frame, anchor="nw")
    symptoms_canvas.configure(yscrollcommand=symptoms_scrollbar.set)
    
    tk.Label(symptoms_inner_frame, text="Belirtiler:", font=("Arial", 12, "bold")).pack(anchor="w")
    for s_id, s_name in symptoms_options:
        var = tk.BooleanVar()
        cb = tk.Checkbutton(symptoms_inner_frame, text=s_name, variable=var, font=("Arial", 10))
        cb.pack(anchor="w", padx=20)
        symptom_vars[s_id] = var
    
    symptoms_canvas.pack(side="left", fill="both", expand=True)
    symptoms_scrollbar.pack(side="right", fill="y")
    
    tk.Label(main_frame, text="Belirti Kayıt Tarihi:", font=("Arial", 12)).pack(pady=(10,0))
    kayit_tarihi_entry = DateEntry(main_frame, width=18, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
    kayit_tarihi_entry.set_date(datetime.date.today())
    kayit_tarihi_entry.pack(pady=5)

    tk.Label(main_frame, text="Şiddet Seviyesi:", font=("Arial", 12)).pack(pady=(10,0))
    siddet_var = tk.StringVar(main_frame)
    siddet_options_list = ["Hafif", "Orta", "Şiddetli"]
    siddet_var.set("Orta")
    siddet_menu = tk.OptionMenu(main_frame, siddet_var, *siddet_options_list)
    siddet_menu.config(width=15)
    siddet_menu.pack(pady=5)

    tk.Label(main_frame, text="Doktor Notu (Opsiyonel):", font=("Arial", 12)).pack(pady=(10,0))
    notes_entry = tk.Entry(main_frame, width=50)
    notes_entry.pack(pady=5)

    def assign_symptoms():
        tc_kimlik_no = patient_tc_entry.get().strip()
        if not tc_kimlik_no.isdigit() or len(tc_kimlik_no) != 11:
            messagebox.showerror("Hata", "Lütfen geçerli bir T.C. Kimlik No girin.", parent=parent_window)
            return

        selected_s_ids = [s_id for s_id, var_ in symptom_vars.items() if var_.get()]
        if not selected_s_ids:
            messagebox.showwarning("Uyarı", "Lütfen en az bir belirti seçin.", parent=parent_window)
            return
        
        try:
            kayit_tarihi_str = kayit_tarihi_entry.get_date().strftime('%Y-%m-%d')
        except Exception:
            messagebox.showerror("Hata", "Geçerli bir kayıt tarihi girin (GG.AA.YYYY).", parent=parent_window)
            return

        siddet = siddet_var.get()
        notes = notes_entry.get().strip()

        conn = connect_db()
        if not conn: return
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = %s", (tc_kimlik_no,))
            patient_result = cursor.fetchone()
            if not patient_result:
                messagebox.showerror("Hata", "Belirtilen T.C. Kimlik Numarasına sahip hasta bulunamadı.", parent=parent_window)
                return
            target_hasta_id = patient_result['hasta_id']

            for belirti_id_val in selected_s_ids:
                cursor.execute("""
                    INSERT INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi, siddet_seviyesi, notlar, doktor_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE siddet_seviyesi = VALUES(siddet_seviyesi), notlar = VALUES(notlar), doktor_id = VALUES(doktor_id)
                """, (target_hasta_id, belirti_id_val, kayit_tarihi_str, siddet, notes, current_user_doctor_id))
            conn.commit()
            messagebox.showinfo("Başarılı", f"Belirtiler {tc_kimlik_no} T.C. Numaralı hastaya {kayit_tarihi_entry.get_date().strftime('%d.%m.%Y')} tarihi için başarıyla atandı/güncellendi.", parent=parent_window)
            patient_tc_entry.delete(0, tk.END)
            for var_ in symptom_vars.values(): var_.set(False)
            notes_entry.delete(0, tk.END)
            kayit_tarihi_entry.set_date(datetime.date.today())


        except mysql.connector.Error as err:
            conn.rollback()
            messagebox.showerror("Veritabanı Hatası", f"Belirtiler atanırken hata oluştu: {err}", parent=parent_window)
        finally:
            cursor.close()
            conn.close()

    tk.Button(main_frame, text="Belirtileri Ata/Güncelle", command=assign_symptoms,
              width=30, height=2, font=("Arial", 12), bg="blue", fg="white").pack(pady=20)
    tk.Button(main_frame, text="Geri", command=lambda: show_add_to_system_options(parent_window),
              width=20, height=2, font=("Arial", 10)).pack(pady=10)


def manage_exercise_recommendations(parent_window):
    clear_window(parent_window)
    parent_window.title("Doktor: Hastaya Egzersiz Planı Ata")
    parent_window.geometry("600x600")

    main_frame = tk.Frame(parent_window, padx=20, pady=20)
    main_frame.pack(expand=True, fill="both")

    tk.Label(main_frame, text="Hastaya Egzersiz Planı Ata", font=("Arial", 16, "bold")).pack(pady=10)

    tk.Label(main_frame, text="Hastanın T.C. Kimlik Numarası:", font=("Arial", 12)).pack(pady=5)
    patient_tc_entry = tk.Entry(main_frame, width=30)
    patient_tc_entry.pack(pady=5)
    patient_tc_entry.focus_set()

    egzersiz_options_db = get_egzersiz_turleri() 
    egzersiz_names = [name for id, name in egzersiz_options_db]
    egzersiz_map = {name: id for id, name in egzersiz_options_db}

    tk.Label(main_frame, text="Egzersiz Türü:", font=("Arial", 12)).pack(pady=5)
    selected_egzersiz_var = tk.StringVar(main_frame)
    if egzersiz_names:
        selected_egzersiz_var.set(egzersiz_names[0])
    else:
        tk.Label(main_frame, text="Sistemde egzersiz türü bulunmuyor!", fg="red").pack()
        tk.Button(main_frame, text="Geri", command=lambda: show_add_to_system_options(parent_window)).pack(pady=10)
        return
        
    egzersiz_menu = tk.OptionMenu(main_frame, selected_egzersiz_var, *egzersiz_names)
    egzersiz_menu.config(width=30)
    egzersiz_menu.pack(pady=5)

    tk.Label(main_frame, text="Haftalık Sıklık (örn: 3 gün):", font=("Arial", 12)).pack(pady=5)
    siklik_entry = tk.Entry(main_frame, width=10)
    siklik_entry.insert(0, "3")
    siklik_entry.pack(pady=5)

    tk.Label(main_frame, text="Süre (dakika - örn: 30 dk):", font=("Arial", 12)).pack(pady=5)
    sure_entry = tk.Entry(main_frame, width=10)
    sure_entry.insert(0, "30")
    sure_entry.pack(pady=5)

    tk.Label(main_frame, text="Başlangıç Tarihi:", font=("Arial", 12)).pack(pady=5)
    baslangic_tarihi_entry = DateEntry(main_frame, width=18, date_pattern='dd.mm.yyyy')
    baslangic_tarihi_entry.set_date(datetime.date.today())
    baslangic_tarihi_entry.pack(pady=5)

    tk.Label(main_frame, text="Bitiş Tarihi (Opsiyonel):", font=("Arial", 12)).pack(pady=5)
    bitis_tarihi_entry = DateEntry(main_frame, width=18, date_pattern='dd.mm.yyyy')
    bitis_tarihi_entry.delete(0, tk.END) 
    bitis_tarihi_entry.pack(pady=5)


    def assign_exercise():
        tc_kimlik_no = patient_tc_entry.get().strip()
        if not tc_kimlik_no.isdigit() or len(tc_kimlik_no) != 11:
            messagebox.showerror("Hata", "Lütfen geçerli bir T.C. Kimlik No girin.", parent=parent_window)
            return

        selected_egzersiz_name = selected_egzersiz_var.get()
        if not selected_egzersiz_name:  
            messagebox.showwarning("Uyarı", "Lütfen bir egzersiz türü seçin.", parent=parent_window)
            return
        egzersiz_turu_id = egzersiz_map.get(selected_egzersiz_name)

        try:
            haftalik_siklik = int(siklik_entry.get())
            sure_dakika = int(sure_entry.get())
            if haftalik_siklik <=0 or sure_dakika <=0:
                raise ValueError("Sıklık ve süre pozitif olmalı.")
        except ValueError as ve:
            messagebox.showerror("Hata", f"Geçerli sıklık ve süre girin: {ve}", parent=parent_window)
            return
        
        try:
            baslangic_tarihi_str = baslangic_tarihi_entry.get_date().strftime('%Y-%m-%d')
            bitis_tarihi_str_input = bitis_tarihi_entry.get() 
            bitis_tarihi_str = None
            if bitis_tarihi_str_input: 
                 bitis_tarihi_str = bitis_tarihi_entry.get_date().strftime('%Y-%m-%d')
            
            if bitis_tarihi_str and baslangic_tarihi_str > bitis_tarihi_str:
                messagebox.showerror("Hata", "Bitiş tarihi başlangıç tarihinden önce olamaz.", parent=parent_window)
                return

        except Exception as date_err:
            messagebox.showerror("Hata", f"Geçerli başlangıç/bitiş tarihi girin: {date_err}", parent=parent_window)
            return


        conn = connect_db()
        if not conn: return
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = %s", (tc_kimlik_no,))
            patient_result = cursor.fetchone()
            if not patient_result:
                messagebox.showerror("Hata", "Belirtilen T.C. Kimlik Numarasına sahip hasta bulunamadı.", parent=parent_window)
                conn.close()
                return
            target_hasta_id = patient_result['hasta_id']

            cursor.execute("""
                UPDATE egzersiz_planlari SET aktif_durum = FALSE, bitis_tarihi = DATE_SUB(%s, INTERVAL 1 DAY)
                WHERE hasta_id = %s AND aktif_durum = TRUE AND (bitis_tarihi IS NULL OR bitis_tarihi >= %s)
            """, (baslangic_tarihi_str, target_hasta_id, baslangic_tarihi_str))


            cursor.execute("""
                INSERT INTO egzersiz_planlari 
                (hasta_id, doktor_id, egzersiz_turu_id, baslangic_tarihi, bitis_tarihi, haftalik_siklik, sure_dakika, aktif_durum)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            """, (target_hasta_id, current_user_doctor_id, egzersiz_turu_id, baslangic_tarihi_str, bitis_tarihi_str, haftalik_siklik, sure_dakika))
            conn.commit()
            messagebox.showinfo("Başarılı", f"Egzersiz planı {tc_kimlik_no} T.C. Numaralı hastaya başarıyla atandı.", parent=parent_window)
            patient_tc_entry.delete(0, tk.END)


        except mysql.connector.Error as err:
            conn.rollback()
            messagebox.showerror("Veritabanı Hatası", f"Egzersiz planı atanırken hata oluştu: {err}", parent=parent_window)
        finally:
            cursor.close()
            conn.close()

    tk.Button(main_frame, text="Egzersiz Planını Ata", command=assign_exercise,
              width=30, height=2, font=("Arial", 12), bg="orange", fg="white").pack(pady=20)
    tk.Button(main_frame, text="Geri", command=lambda: show_add_to_system_options(parent_window),
              width=20, height=2, font=("Arial", 10)).pack(pady=10)


def manage_diet_plans(parent_window):
    clear_window(parent_window)
    parent_window.title("Doktor: Hastaya Beslenme Planı Ata")
    parent_window.geometry("600x500")

    main_frame = tk.Frame(parent_window, padx=20, pady=20)
    main_frame.pack(expand=True, fill="both")

    tk.Label(main_frame, text="Hastaya Beslenme Planı Ata", font=("Arial", 16, "bold")).pack(pady=10)

    tk.Label(main_frame, text="Hastanın T.C. Kimlik Numarası:", font=("Arial", 12)).pack(pady=5)
    patient_tc_entry = tk.Entry(main_frame, width=30)
    patient_tc_entry.pack(pady=5)
    patient_tc_entry.focus_set()

    diyet_options_db = get_diyet_turleri()
    diyet_names = [name for id, name in diyet_options_db]
    diyet_map = {name: id for id, name in diyet_options_db}

    tk.Label(main_frame, text="Diyet Türü:", font=("Arial", 12)).pack(pady=5)
    selected_diyet_var = tk.StringVar(main_frame)
    if diyet_names:
        selected_diyet_var.set(diyet_names[0])
    else:
        tk.Label(main_frame, text="Sistemde diyet türü bulunmuyor!", fg="red").pack()
        tk.Button(main_frame, text="Geri", command=lambda: show_add_to_system_options(parent_window)).pack(pady=10)
        return

    diyet_menu = tk.OptionMenu(main_frame, selected_diyet_var, *diyet_names)
    diyet_menu.config(width=30)
    diyet_menu.pack(pady=5)

    tk.Label(main_frame, text="Başlangıç Tarihi:", font=("Arial", 12)).pack(pady=5)
    baslangic_tarihi_entry = DateEntry(main_frame, width=18,date_pattern='dd.mm.yyyy')
    baslangic_tarihi_entry.set_date(datetime.date.today())
    baslangic_tarihi_entry.pack(pady=5)
    
    tk.Label(main_frame, text="Bitiş Tarihi (Opsiyonel):", font=("Arial", 12)).pack(pady=5)
    bitis_tarihi_entry = DateEntry(main_frame, width=18,date_pattern='dd.mm.yyyy')
    bitis_tarihi_entry.delete(0, tk.END) 
    bitis_tarihi_entry.pack(pady=5)

    def assign_diet():
        tc_kimlik_no = patient_tc_entry.get().strip()
        if not tc_kimlik_no.isdigit() or len(tc_kimlik_no) != 11:
            messagebox.showerror("Hata", "Lütfen geçerli bir T.C. Kimlik No girin.", parent=parent_window)
            return

        selected_diyet_name = selected_diyet_var.get()
        if not selected_diyet_name:
            messagebox.showwarning("Uyarı", "Lütfen bir diyet türü seçin.", parent=parent_window)
            return
        diyet_turu_id = diyet_map.get(selected_diyet_name)

        try:
            baslangic_tarihi_str = baslangic_tarihi_entry.get_date().strftime('%Y-%m-%d')
            bitis_tarihi_str_input = bitis_tarihi_entry.get()
            bitis_tarihi_str = None
            if bitis_tarihi_str_input:
                bitis_tarihi_str = bitis_tarihi_entry.get_date().strftime('%Y-%m-%d')
            if bitis_tarihi_str and baslangic_tarihi_str > bitis_tarihi_str:
                messagebox.showerror("Hata", "Bitiş tarihi başlangıç tarihinden önce olamaz.", parent=parent_window)
                return
        except Exception as date_err:
            messagebox.showerror("Hata", f"Geçerli başlangıç/bitiş tarihi girin: {date_err}", parent=parent_window)
            return

        conn = connect_db()
        if not conn: return
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = %s", (tc_kimlik_no,))
            patient_result = cursor.fetchone()
            if not patient_result:
                messagebox.showerror("Hata", "Belirtilen T.C. Kimlik Numarasına sahip hasta bulunamadı.", parent=parent_window)
                conn.close()
                return
            target_hasta_id = patient_result['hasta_id']

            cursor.execute("""
                UPDATE diyet_planlari SET aktif_durum = FALSE, bitis_tarihi = DATE_SUB(%s, INTERVAL 1 DAY) 
                WHERE hasta_id = %s AND aktif_durum = TRUE AND (bitis_tarihi IS NULL OR bitis_tarihi >= %s)
            """, (baslangic_tarihi_str, target_hasta_id, baslangic_tarihi_str))


            cursor.execute("""
                INSERT INTO diyet_planlari 
                (hasta_id, doktor_id, diyet_turu_id, baslangic_tarihi, bitis_tarihi, aktif_durum)
                VALUES (%s, %s, %s, %s, %s, TRUE)
            """, (target_hasta_id, current_user_doctor_id, diyet_turu_id, baslangic_tarihi_str, bitis_tarihi_str))
            conn.commit()
            messagebox.showinfo("Başarılı", f"Beslenme planı {tc_kimlik_no} T.C. Numaralı hastaya başarıyla atandı.", parent=parent_window)
            patient_tc_entry.delete(0, tk.END)

        except mysql.connector.Error as err:
            conn.rollback()
            messagebox.showerror("Veritabanı Hatası", f"Beslenme planı atanırken hata oluştu: {err}", parent=parent_window)
        finally:
            cursor.close()
            conn.close()

    tk.Button(main_frame, text="Beslenme Planını Ata", command=assign_diet,
              width=30, height=2, font=("Arial", 12), bg="purple", fg="white").pack(pady=20)
    tk.Button(main_frame, text="Geri", command=lambda: show_add_to_system_options(parent_window),
              width=20, height=2, font=("Arial", 10)).pack(pady=10)

def show_doctor_patients_with_filters(parent_window):
    patients_window = tk.Toplevel(parent_window)
    patients_window.title("Hastalarım ve Filtreleme")
    patients_window.geometry("950x700")

    filter_frame = tk.Frame(patients_window, pady=10)
    filter_frame.pack(fill="x", padx=10)

    tk.Label(filter_frame, text="Filtreler:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    tk.Label(filter_frame, text="Ad/Soyad/TC:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=2, sticky="w")
    name_filter_entry = tk.Entry(filter_frame, width=20)
    name_filter_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

    tk.Label(filter_frame, text="Min KS (Son Ölçüm):", font=("Arial", 10)).grid(row=1, column=2, padx=5, pady=2, sticky="w")
    min_bs_filter_entry = tk.Entry(filter_frame, width=7)
    min_bs_filter_entry.grid(row=1, column=3, padx=5, pady=2, sticky="w")

    tk.Label(filter_frame, text="Max KS (Son Ölçüm):", font=("Arial", 10)).grid(row=1, column=4, padx=5, pady=2, sticky="w")
    max_bs_filter_entry = tk.Entry(filter_frame, width=7)
    max_bs_filter_entry.grid(row=1, column=5, padx=5, pady=2, sticky="w")
    
    symptom_options = get_symptom_options()
    symptom_filter_var = tk.StringVar(filter_frame)
    symptom_names_for_filter = ["Tüm Belirtiler"] + [s[1] for s in symptom_options]
    symptom_id_map = {name: id for id, name in symptom_options}
    symptom_filter_var.set("Tüm Belirtiler")

    tk.Label(filter_frame, text="Belirti (Son Kayıt):", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=2, sticky="w")
    symptom_filter_menu = tk.OptionMenu(filter_frame, symptom_filter_var, *symptom_names_for_filter)
    symptom_filter_menu.grid(row=2, column=1, padx=5, pady=2, sticky="ew", columnspan=2)

    list_frame = tk.Frame(patients_window)
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    canvas = tk.Canvas(list_frame)
    scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def populate_patient_list():
        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        conn = connect_db()
        if not conn: return
        cursor = conn.cursor(dictionary=True)
        
        query_parts = [f"""
        SELECT DISTINCT h.hasta_id, k.ad, k.soyad, k.tc_kimlik_no, h.diyabet_tipi, h.tani_tarihi,
        (SELECT kso.kan_sekeri_degeri FROM kan_sekeri_olcumleri kso WHERE kso.hasta_id = h.hasta_id ORDER BY kso.olcum_zamani DESC LIMIT 1) as son_kan_sekeri,
        (SELECT GROUP_CONCAT(b.belirti_adi SEPARATOR ', ') FROM hasta_belirtileri hb JOIN belirtiler b ON hb.belirti_id = b.belirti_id WHERE hb.hasta_id = h.hasta_id AND hb.kayit_tarihi = (SELECT MAX(hb_inner.kayit_tarihi) FROM hasta_belirtileri hb_inner WHERE hb_inner.hasta_id = h.hasta_id) ) as son_belirtiler
        FROM hastalar h
        JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
        WHERE h.doktor_id = %s
        """]
        params = [current_user_doctor_id]

        name_filter = name_filter_entry.get().strip()
        min_bs_filter_str = min_bs_filter_entry.get().strip()
        max_bs_filter_str = max_bs_filter_entry.get().strip()
        selected_symptom_name = symptom_filter_var.get()

        if name_filter:
            query_parts.append("AND (k.ad LIKE %s OR k.soyad LIKE %s OR k.tc_kimlik_no LIKE %s OR CONCAT(k.ad, ' ', k.soyad) LIKE %s)")
            like_term = f"%{name_filter}%"
            params.extend([like_term, like_term, like_term, like_term])
        
        
        having_clauses = []
        if min_bs_filter_str:
            try:
                min_val = float(min_bs_filter_str)
                having_clauses.append(f"(SELECT kso_filter.kan_sekeri_degeri FROM kan_sekeri_olcumleri kso_filter WHERE kso_filter.hasta_id = h.hasta_id ORDER BY kso_filter.olcum_zamani DESC LIMIT 1) >= {min_val}")
            except ValueError: messagebox.showwarning("Filtre Hatası", "Min Kan Şekeri sayı olmalıdır.", parent=patients_window)
        
        if max_bs_filter_str:
            try:
                max_val = float(max_bs_filter_str)
                having_clauses.append(f"(SELECT kso_filter.kan_sekeri_degeri FROM kan_sekeri_olcumleri kso_filter WHERE kso_filter.hasta_id = h.hasta_id ORDER BY kso_filter.olcum_zamani DESC LIMIT 1) <= {max_val}")
            except ValueError: messagebox.showwarning("Filtre Hatası", "Max Kan Şekeri sayı olmalıdır.", parent=patients_window)

        if selected_symptom_name != "Tüm Belirtiler":
            s_id_to_filter = symptom_id_map.get(selected_symptom_name)
            if s_id_to_filter:
                query_parts.append(f"AND EXISTS (SELECT 1 FROM hasta_belirtileri hb_filter WHERE hb_filter.hasta_id = h.hasta_id AND hb_filter.belirti_id = {s_id_to_filter} AND hb_filter.kayit_tarihi = (SELECT MAX(hb_inner2.kayit_tarihi) FROM hasta_belirtileri hb_inner2 WHERE hb_inner2.hasta_id = h.hasta_id) )")

            
            if min_bs_filter_str:
                try:
                    min_val = float(min_bs_filter_str)
                    final_query_temp += f" AND son_kan_sekeri >= {min_val}"
                except ValueError: pass
            if max_bs_filter_str:
                try:
                    max_val = float(max_bs_filter_str)
                    final_query_temp += f" AND son_kan_sekeri <= {max_val}"
                except ValueError: pass
            query_parts = [final_query_temp.replace("HAVING 1=1 AND", "HAVING").replace("HAVING 1=1", "")]


        final_query = " ".join(query_parts)
        final_query += " ORDER BY k.ad, k.soyad"
        
        try:
            cursor.execute(final_query, tuple(params))
            patients = cursor.fetchall()

            if patients:
                for patient in patients:
                    patient_frame = tk.LabelFrame(scrollable_frame, text=f"{patient['ad']} {patient['soyad']} (TC: {patient['tc_kimlik_no']})",
                                                  font=("Arial", 10, "bold"), padx=10, pady=3)
                    patient_frame.pack(fill="x", padx=5, pady=3)
                    
                    info_text = f"Diyabet Tipi: {patient['diyabet_tipi'] or 'N/A'}"
                    if patient['tani_tarihi']: info_text += f" | Tanı: {patient['tani_tarihi'].strftime('%d.%m.%Y')}"
                    if patient['son_kan_sekeri'] is not None: info_text += f" | Son KS: {patient['son_kan_sekeri']} mg/dL"
                    if patient['son_belirtiler']: info_text += f" | Son Belirtiler: {patient['son_belirtiler'][:50]}..." 
                    
                    tk.Label(patient_frame, text=info_text, anchor="w", justify=tk.LEFT, wraplength=700).pack(fill="x")
                    tk.Button(patient_frame, text="Detayları Görüntüle",
                              command=lambda p_id=patient['hasta_id']: show_patient_details_for_doctor(patients_window, p_id),
                              width=18, bg="lightblue", font=("Arial",9)).pack(pady=3, anchor="e")
            else:
                tk.Label(scrollable_frame, text="Filtre kriterlerine uygun hasta bulunamadı veya size atanmış hasta yok.", font=("Arial", 12)).pack(pady=50)
        
        except mysql.connector.Error as db_err:
            messagebox.showerror("Veritabanı Hatası", f"Hastalar çekilirken hata oluştu: {db_err}\nSorgu: {cursor.statement}", parent=patients_window)
        except Exception as e:
            messagebox.showerror("Hata", f"Hastaları listelerken hata oluştu: {e}", parent=patients_window)
        finally:
            cursor.close()
            conn.close()
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    filter_button = tk.Button(filter_frame, text="Filtrele/Yenile", command=populate_patient_list, width=15)
    filter_button.grid(row=2, column=3, padx=10, pady=5, columnspan=3, sticky="e")
    
    populate_patient_list()

def show_patient_details_for_doctor(parent_window, hasta_id):
    details_window = tk.Toplevel(parent_window)
    details_window.title("Hasta Detayları")
    details_window.geometry("1100x750") 

    conn = connect_db()
    if not conn: return

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT k.ad, k.soyad, k.tc_kimlik_no, h.diyabet_tipi, h.hedef_kan_sekeri_min, h.hedef_kan_sekeri_max
            FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
            WHERE h.hasta_id = %s
        """, (hasta_id,))
        patient_info = cursor.fetchone()

        if not patient_info:
            messagebox.showerror("Hata", "Hasta bulunamadı.", parent=details_window)
            details_window.destroy()
            conn.close()
            return

        tk.Label(details_window, text=f"{patient_info['ad']} {patient_info['soyad']} (TC: {patient_info['tc_kimlik_no']}) Detayları",
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        header_info_frame = tk.Frame(details_window)
        header_info_frame.pack(fill="x", padx=10)
        tk.Label(header_info_frame, text=f"Diyabet Tipi: {patient_info['diyabet_tipi']}", font=("Arial", 11)).pack(side="left", padx=5)
        tk.Label(header_info_frame, text=f"Hedef Kan Şekeri: {patient_info['hedef_kan_sekeri_min']}-{patient_info['hedef_kan_sekeri_max']} mg/dL", font=("Arial", 11)).pack(side="left", padx=5)

        notebook = ttk.Notebook(details_window)
        notebook.pack(pady=10, expand=True, fill="both")

        bs_frame = tk.Frame(notebook)
        notebook.add(bs_frame, text="Kan Şekeri Geçmişi ve Grafik")
        load_blood_sugar_history_for_doctor(bs_frame, hasta_id) 

        de_frame = tk.Frame(notebook)
        notebook.add(de_frame, text="Diyet/Egz. Geçmişi ve Uyum (%)") 
        load_diet_exercise_history_for_doctor(de_frame, hasta_id) 

        sym_frame = tk.Frame(notebook)
        notebook.add(sym_frame, text="Semptom Geçmişi")
        load_symptom_history_for_doctor(sym_frame, hasta_id)

        ins_frame = tk.Frame(notebook)
        notebook.add(ins_frame, text="İnsülin Önerileri (Hasta Bildirimi)")
        load_insulin_recommendations_for_doctor(ins_frame, hasta_id)
        
        auto_recommend_frame = tk.Frame(notebook)
        notebook.add(auto_recommend_frame, text="Otomatik Diyet/Egzersiz Önerisi")
        setup_automatic_recommendation_display(auto_recommend_frame, hasta_id, patient_info['ad'] + " " + patient_info['soyad'])


        notes_frame = tk.Frame(notebook)
        notebook.add(notes_frame, text="Doktor Notları")
        load_doctor_notes_for_patient(notes_frame, hasta_id)

    except Exception as e:
        messagebox.showerror("Hata", f"Hasta detayları yüklenirken hata oluştu: {e}", parent=details_window)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def setup_automatic_recommendation_display(parent_frame, hasta_id, hasta_adi_soyadi):
    for widget in parent_frame.winfo_children(): widget.destroy()

    tk.Label(parent_frame, text=f"{hasta_adi_soyadi} için Kural Tabanlı Diyet ve Egzersiz Önerisi", font=("Arial", 12, "bold")).pack(pady=10)
    
    info_label = tk.Label(parent_frame, text="Öneri almak için hastanın güncel kan şekeri ve bugüne ait belirti bilgileri gereklidir.\nBelirtiler, 'Hastaya Plan/Belirti Ata' menüsünden doktor tarafından girilmelidir.", 
                          font=("Arial", 9), justify=tk.LEFT, fg="blue")
    info_label.pack(pady=5, padx=10)

    recommendation_text_area = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=80, height=15, font=("Arial", 10))
    recommendation_text_area.pack(pady=10, padx=10, fill="both", expand=True)
    recommendation_text_area.config(state=tk.DISABLED)

    def get_and_show_recommendation():
        recommendation_text_area.config(state=tk.NORMAL)
        recommendation_text_area.delete("1.0", tk.END)

        conn_rec = connect_db()
        if not conn_rec: 
            recommendation_text_area.insert(tk.END, "Veritabanı bağlantı hatası.")
            recommendation_text_area.config(state=tk.DISABLED)
            return
            
        cursor_rec = conn_rec.cursor(dictionary=True)
        try:
            cursor_rec.execute("""
                SELECT kan_sekeri_degeri FROM kan_sekeri_olcumleri 
                WHERE hasta_id = %s ORDER BY olcum_zamani DESC LIMIT 1
            """, (hasta_id,))
            bs_record = cursor_rec.fetchone()
            if not bs_record:
                recommendation_text_area.insert(tk.END, "Hastanın kayıtlı kan şekeri ölçümü bulunmuyor. Öneri üretilemedi.")
                recommendation_text_area.config(state=tk.DISABLED)
                conn_rec.close()
                return
            current_blood_sugar = bs_record['kan_sekeri_degeri']

            cursor_rec.execute("""
                SELECT DISTINCT b.belirti_adi 
                FROM hasta_belirtileri hb
                JOIN belirtiler b ON hb.belirti_id = b.belirti_id
                WHERE hb.hasta_id = %s AND hb.kayit_tarihi = CURDATE() AND hb.doktor_id IS NOT NULL
            """, (hasta_id,))
            symptoms_records = cursor_rec.fetchall()
            patient_symptoms_list = [s['belirti_adi'] for s in symptoms_records]
            patient_symptoms_json = json.dumps(patient_symptoms_list)

            öneri_mesaji_header = (f"Hastanın Durumu (Öneri İçin Kullanılan):\n"
                                   f"  Son Kan Şekeri: {current_blood_sugar} mg/dL\n"
                                   f"  Bugün Doktor Tarafından Girilen Belirtiler: {', '.join(patient_symptoms_list) if patient_symptoms_list else 'Yok veya Girilmemiş'}\n\n")
            recommendation_text_area.insert(tk.END, öneri_mesaji_header)

            if not patient_symptoms_list: 
                 recommendation_text_area.insert(tk.END, "Doktor tarafından bugün için belirti girişi yapılmamış. Lütfen önce belirtileri girin.\n")


            cursor_rec.callproc('kural_tabanli_oneri_getir', [current_blood_sugar, patient_symptoms_json])
            
            recommendation_result = None
            for result in cursor_rec.stored_results():
                recommendation_data = result.fetchall() 
                if recommendation_data:
                    recommendation_result = recommendation_data[0] 
                    break
            
            if recommendation_result and recommendation_result.get('onerilen_diyet'): 
                diyet_onerisi = recommendation_result.get('onerilen_diyet', "Belirtilmemiş")
                egzersiz_onerisi = recommendation_result.get('onerilen_egzersiz', "Belirtilmemiş")
                
                öneri_mesaji_body = (f"Otomatik Sistem Önerisi:\n"
                                     f"  Önerilen Diyet: {diyet_onerisi}\n"
                                     f"  Önerilen Egzersiz: {egzersiz_onerisi if egzersiz_onerisi else 'Yok'}\n\n"
                                     f"Bu öneriyi hastanın planına eklemek için 'Hastaya Plan/Belirti Ata' menüsünden ilgili plan atama ekranlarını kullanabilirsiniz.")
                recommendation_text_area.insert(tk.END, öneri_mesaji_body)
            else:
                recommendation_text_area.insert(tk.END, "Mevcut kan şekeri ve belirtilere uygun otomatik bir diyet/egzersiz önerisi kural tabanında bulunamadı.")
            
        except mysql.connector.Error as err:
            recommendation_text_area.insert(tk.END, f"Öneri alınırken veritabanı hatası: {err}")
        except Exception as e:
            recommendation_text_area.insert(tk.END, f"Öneri alınırken bir program hatası oluştu: {e}")
        finally:
            if conn_rec.is_connected():
                cursor_rec.close()
                conn_rec.close()
            recommendation_text_area.config(state=tk.DISABLED)

    tk.Button(parent_frame, text="Otomatik Diyet/Egzersiz Önerisi Al", command=get_and_show_recommendation,
              width=35, height=2, font=("Arial", 11), bg="teal", fg="white").pack(pady=10)

def load_blood_sugar_history_for_doctor(parent_frame, hasta_id):
    for widget in parent_frame.winfo_children(): widget.destroy()

    tk.Label(parent_frame, text="Son Kan Şekeri Ölçümleri:", font=("Arial", 11, "bold")).pack(pady=5, anchor="w", padx=10)
    text_area = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=80, height=10, font=("Arial", 10))
    text_area.pack(pady=5, padx=10, fill="x")

    conn = connect_db()
    if not conn: 
        text_area.insert(tk.END, "Veritabanı bağlantı hatası.")
        text_area.config(state=tk.DISABLED)
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT olcum_tarihi, olcum_saati, kan_sekeri_degeri, olcum_tipi, gecerli_olcum
            FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s
            ORDER BY olcum_tarihi DESC, olcum_saati DESC
            LIMIT 50
        """, (hasta_id,))
        measurements = cursor.fetchall()

        if measurements:
            for m in measurements:
                valid_status = "Geçerli (Ort. Dahil)" if m['gecerli_olcum'] else "Saat Dışı (Ort. Hariç)"
                text_area.insert(tk.END, f"{m['olcum_tarihi'].strftime('%d.%m.%Y')} {m['olcum_saati'].strftime('%H:%M')} - {m['olcum_tipi']}: {m['kan_sekeri_degeri']} mg/dL ({valid_status})\n")
        else:
            text_area.insert(tk.END, "Bu hastaya ait kan şekeri ölçümü bulunmamaktadır.")
        text_area.config(state=tk.DISABLED)

        plot_blood_sugar_trend(parent_frame, hasta_id)

    except Exception as e:
        messagebox.showerror("Hata", f"Kan şekeri geçmişi yüklenirken hata oluştu: {e}", parent=parent_frame)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def plot_blood_sugar_trend(parent_frame, hasta_id):
    
    for widget in parent_frame.winfo_children():
        if isinstance(widget, tk.Canvas): 
            widget.destroy()
            break 

    conn = connect_db()
    if not conn: return
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT olcum_zamani, kan_sekeri_degeri
            FROM kan_sekeri_olcumleri
            WHERE hasta_id = %s AND gecerli_olcum = TRUE
            ORDER BY olcum_zamani ASC
            LIMIT 100 
        """, (hasta_id,))
        data = cursor.fetchall()

        if data:
            dates = [item['olcum_zamani'] for item in data]
            values = [float(item['kan_sekeri_degeri']) for item in data]

            fig = Figure(figsize=(9, 3.5), dpi=100) 
            ax = fig.add_subplot(111)
            ax.plot(dates, values, marker='o', linestyle='-', color='deepskyblue', label="Kan Şekeri")

            cursor.execute("SELECT hedef_kan_sekeri_min, hedef_kan_sekeri_max FROM hastalar WHERE hasta_id = %s", (hasta_id,))
            target_range = cursor.fetchone()
            if target_range:
                ax.axhspan(target_range['hedef_kan_sekeri_min'], target_range['hedef_kan_sekeri_max'], color='palegreen', alpha=0.4, label=f"Hedef ({target_range['hedef_kan_sekeri_min']}-{target_range['hedef_kan_sekeri_max']})")
            
            ax.set_title('Kan Şekeri Değişim Grafiği (Son 100 Geçerli Ölçüm)')
            ax.set_xlabel('Tarih ve Saat')
            ax.set_ylabel('Kan Şekeri (mg/dL)')
            ax.legend(fontsize='small')
            ax.grid(True, linestyle=':')
            
            formatter = DateFormatter('%d.%m %H:%M')
            ax.xaxis.set_major_formatter(formatter)
            fig.autofmt_xdate(rotation=30, ha='right')
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(pady=5, fill="both", expand=True)
            canvas.draw()
        else:
            tk.Label(parent_frame, text="Grafik oluşturmak için yeterli geçerli kan şekeri verisi yok.").pack(pady=10)

    except Exception as e:
        messagebox.showerror("Hata", f"Grafik oluşturulurken hata oluştu: {e}", parent=parent_frame)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def load_diet_exercise_history_for_doctor(parent_frame, hasta_id):
    for widget in parent_frame.winfo_children(): widget.destroy()

    tk.Label(parent_frame, text="Son Diyet ve Egzersiz Takibi:", font=("Arial", 11, "bold")).pack(pady=5, anchor="w", padx=10)
    text_area = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=80, height=8, font=("Arial", 10))
    text_area.pack(pady=5, padx=10, fill="x")

    conn = connect_db()
    if not conn: 
        text_area.insert(tk.END, "Veritabanı bağlantı hatası.")
        text_area.config(state=tk.DISABLED)
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT dt.takip_tarihi, dt.diyet_uygulandimi, et.egzersiz_yapildimi, et.sure_dakika
            FROM diyet_takibi dt
            LEFT JOIN egzersiz_takibi et ON dt.hasta_id = et.hasta_id AND dt.takip_tarihi = et.takip_tarihi
            WHERE dt.hasta_id = %s
            ORDER BY dt.takip_tarihi DESC
            LIMIT 30
        """, (hasta_id,))
        records = cursor.fetchall()

        if records:
            for r in records:
                diyet_status = "Uygulandı" if r['diyet_uygulandimi'] else "Uygulanmadı"
                egzersiz_status = "Yapıldı" if r['egzersiz_yapildimi'] else "Yapılmadı"
                sure_info = f"({r['sure_dakika']} dk)" if r['sure_dakika'] is not None else ""
                text_area.insert(tk.END, f"{r['takip_tarihi'].strftime('%d.%m.%Y')}: Diyet: {diyet_status}, Egzersiz: {egzersiz_status} {sure_info}\n")
        else:
            text_area.insert(tk.END, "Bu hastaya ait diyet ve egzersiz takibi bulunmamaktadır.")
        text_area.config(state=tk.DISABLED)

        plot_compliance_percentages(parent_frame, hasta_id, "Doktor")

    except Exception as e:
        messagebox.showerror("Hata", f"Diyet/egzersiz geçmişi yüklenirken hata oluştu: {e}", parent=parent_frame)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def plot_compliance_percentages(parent_frame, patient_id_for_plot, role_for_title="Hasta"):

    for widget in parent_frame.winfo_children():
        if isinstance(widget, (tk.Canvas, tk.Label)) and hasattr(widget, 'is_compliance_related'):
            widget.destroy()

    conn = connect_db()
    if not conn: return
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT hesaplama_tarihi, diyet_uyum_orani, egzersiz_uyum_orani, olcum_uyum_orani, genel_uyum_skoru
            FROM hasta_uyum_skorlari
            WHERE hasta_id = %s
            ORDER BY hesaplama_tarihi DESC 
            LIMIT 30 
        """, (patient_id_for_plot,))
        data = cursor.fetchall()
        data.reverse() 

        if data:
            dates = [d['hesaplama_tarihi'].strftime('%d.%m') for d in data]
            diet_compliance = [d['diyet_uyum_orani'] for d in data]
            exercise_compliance = [d['egzersiz_uyum_orani'] for d in data]
            measurement_compliance = [d['olcum_uyum_orani'] for d in data]
            overall_compliance = [d['genel_uyum_skoru'] for d in data]

            fig = Figure(figsize=(9, 3.5), dpi=100) 
            ax = fig.add_subplot(111)

            ax.plot(dates, diet_compliance, marker='o', linestyle='-', label='Diyet Uyum (%)')
            ax.plot(dates, exercise_compliance, marker='x', linestyle='-', label='Egzersiz Uyum (%)')
            ax.plot(dates, measurement_compliance, marker='s', linestyle='-', label='Ölçüm Uyum (%)')
            ax.plot(dates, overall_compliance, marker='^', linestyle='--', label='Genel Uyum Skoru (%)', color='black', linewidth=1.5)

            ax.set_title(f'{role_for_title} - Son 30 Günlük Uyum Skorları (%)')
            ax.set_xlabel('Tarih')
            ax.set_ylabel('Uyum Oranı (%)')
            ax.set_ylim(0, 105) 
            ax.legend(fontsize='x-small')
            ax.grid(True, linestyle=':', alpha=0.7)
            fig.autofmt_xdate(rotation=45, ha='right')
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.is_compliance_related = True 
            canvas_widget.pack(pady=5, fill="both", expand=True)
            canvas.draw()
        else:
            no_data_label = tk.Label(parent_frame, text="Uyum skorları grafiği için yeterli veri yok.")
            no_data_label.is_compliance_related = True
            no_data_label.pack(pady=10)

    except Exception as e:
        messagebox.showerror("Hata", f"Uyum grafiği oluşturulurken hata oluştu: {e}", parent=parent_frame)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def load_symptom_history_for_doctor(parent_frame, hasta_id):
    for widget in parent_frame.winfo_children(): widget.destroy()

    tk.Label(parent_frame, text="Son Semptom Kayıtları:", font=("Arial", 11, "bold")).pack(pady=5, anchor="w", padx=10)
    text_area = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=80, height=15, font=("Arial", 10))
    text_area.pack(pady=5, padx=10, fill="both", expand=True)

    conn = connect_db()
    if not conn: 
        text_area.insert(tk.END, "Veritabanı bağlantı hatası.")
        text_area.config(state=tk.DISABLED)
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT hb.kayit_tarihi, b.belirti_adi, hb.siddet_seviyesi, hb.notlar, 
                   IF(hb.doktor_id IS NOT NULL, CONCAT(dk.ad, ' ', dk.soyad), 'Hasta Kaydı') as kaydeden
            FROM hasta_belirtileri hb
            JOIN belirtiler b ON hb.belirti_id = b.belirti_id
            LEFT JOIN doktorlar d ON hb.doktor_id = d.doktor_id
            LEFT JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
            WHERE hb.hasta_id = %s
            ORDER BY hb.kayit_tarihi DESC, hb.kayit_zamani DESC
            LIMIT 50
        """, (hasta_id,))
        symptoms = cursor.fetchall()

        if symptoms:
            for s in symptoms:
                note_text = f" (Not: {s['notlar']})" if s['notlar'] else ""
                siddet_text = f" (Şiddet: {s['siddet_seviyesi']})" if s['siddet_seviyesi'] else ""
                text_area.insert(tk.END, f"{s['kayit_tarihi'].strftime('%d.%m.%Y')}: {s['belirti_adi']}{siddet_text} - Kaydeden: {s['kaydeden']}{note_text}\n")
        else:
            text_area.insert(tk.END, "Bu hastaya ait semptom takibi bulunmamaktadır.")
        text_area.config(state=tk.DISABLED)
    except Exception as e:
        messagebox.showerror("Hata", f"Semptom geçmişi yüklenirken hata oluştu: {e}", parent=parent_frame)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def load_insulin_recommendations_for_doctor(parent_frame, hasta_id):
    for widget in parent_frame.winfo_children(): widget.destroy()

    tk.Label(parent_frame, text="Hastanın İnsülin Önerileri (Son 30):", font=("Arial", 11, "bold")).pack(pady=5, anchor="w", padx=10)
    text_area = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=80, height=15, font=("Arial", 10))
    text_area.pack(pady=5, padx=10, fill="both", expand=True)

    conn = connect_db()
    if not conn: 
        text_area.insert(tk.END, "Veritabanı bağlantı hatası.")
        text_area.config(state=tk.DISABLED)
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT tarih, olcum_tipi, ortalama_kan_sekeri, onerilen_doz_ml, uygulandi
            FROM insulin_onerileri
            WHERE hasta_id = %s
            ORDER BY tarih DESC, FIELD(olcum_tipi, 'Gece', 'Akşam', 'İkindi', 'Öğle', 'Sabah') DESC
            LIMIT 30
            """
        cursor.execute(query, (hasta_id,))
        recommendations = cursor.fetchall()

        if recommendations:
            for i, rec in enumerate(recommendations):
                status = "✓ Uygulandı (Hasta Bildirimi)" if rec['uygulandi'] else "⏳ Uygulanmadı (Hasta Bildirimi)"
                rec_text = (f"{i+1}. Tarih: {rec['tarih'].strftime('%d.%m.%Y')} - {rec['olcum_tipi']}\n"
                            f"    Ortalama KS: {rec['ortalama_kan_sekeri']:.1f} mg/dL\n"
                            f"    Önerilen Doz: {rec['onerilen_doz_ml']:.1f} ml\n"
                            f"    Durum: {status}\n")
                text_area.insert(tk.END, rec_text + "-"*30 + "\n")
        else:
            text_area.insert(tk.END, "Bu hastaya ait insülin önerisi bulunmamaktadır.")
        text_area.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Hata", f"İnsülin önerileri yüklenirken hata oluştu: {e}", parent=parent_frame)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def load_doctor_notes_for_patient(parent_frame, hasta_id):
    for widget in parent_frame.winfo_children(): widget.destroy()

    tk.Label(parent_frame, text="Hasta Notları:", font=("Arial", 11, "bold")).pack(pady=5)
    
    notes_display_area = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=80, height=10, font=("Arial", 10))
    notes_display_area.pack(pady=5, padx=10, fill="both", expand=True)

    conn_load = connect_db()
    if not conn_load: 
        notes_display_area.insert(tk.END, "Veritabanı bağlantı hatası.")
        notes_display_area.config(state=tk.DISABLED)
    else:
        cursor_load = conn_load.cursor(dictionary=True)
        try:
            cursor_load.execute("""
                SELECT not_id, not_basligi, not_icerigi, olusturma_tarihi, onem_seviyesi, gorunurluk
                FROM doktor_hasta_notlari
                WHERE hasta_id = %s AND doktor_id = %s
                ORDER BY olusturma_tarihi DESC
            """, (hasta_id, current_user_doctor_id))
            notes = cursor_load.fetchall()

            if notes:
                for note in notes:
                    notes_display_area.insert(tk.END, f"Başlık: {note['not_basligi']} (Önem: {note['onem_seviyesi']}, Görünürlük: {note['gorunurluk']})\n")
                    notes_display_area.insert(tk.END, f"Tarih: {note['olusturma_tarihi'].strftime('%d.%m.%Y %H:%M')}\n")
                    notes_display_area.insert(tk.END, f"İçerik: {note['not_icerigi']}\n")
                    notes_display_area.insert(tk.END, "-" * 50 + "\n\n")
            else:
                notes_display_area.insert(tk.END, "Bu hastaya ait doktor notu bulunmamaktadır.")
        except Exception as e:
            messagebox.showerror("Hata", f"Doktor notları yüklenirken hata oluştu: {e}", parent=parent_frame)
        finally:
            if conn_load.is_connected():
                cursor_load.close()
                conn_load.close()
    notes_display_area.config(state=tk.DISABLED)

    tk.Label(parent_frame, text="Yeni Not Ekle/Güncelle:", font=("Arial", 11, "bold")).pack(pady=(10,5))
    
    form_frame = tk.Frame(parent_frame)
    form_frame.pack(padx=10, fill="x")

    tk.Label(form_frame, text="Başlık:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=2)
    note_title_entry = tk.Entry(form_frame, width=50)
    note_title_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=5)

    tk.Label(form_frame, text="İçerik:", font=("Arial", 10)).grid(row=1, column=0, sticky="nw", pady=2)
    note_content_text = scrolledtext.ScrolledText(form_frame, wrap=tk.WORD, width=50, height=4, font=("Arial", 10))
    note_content_text.grid(row=1, column=1, sticky="ew", pady=2, padx=5)
    
    form_frame.grid_columnconfigure(1, weight=1) 

    options_frame = tk.Frame(parent_frame)
    options_frame.pack(padx=10, fill="x", pady=5)

    tk.Label(options_frame, text="Önem:", font=("Arial", 10)).pack(side="left", padx=(0,5))
    onem_seviyesi_options = ["Düşük", "Orta", "Yüksek"]
    onem_seviyesi_var = tk.StringVar(options_frame)
    onem_seviyesi_var.set("Orta")
    onem_seviyesi_menu = tk.OptionMenu(options_frame, onem_seviyesi_var, *onem_seviyesi_options)
    onem_seviyesi_menu.config(width=8)
    onem_seviyesi_menu.pack(side="left", padx=5)

    tk.Label(options_frame, text="Görünürlük:", font=("Arial", 10)).pack(side="left", padx=(10,5))
    gorunurluk_options = ["Sadece Doktor", "Doktor ve Hasta"]
    gorunurluk_var = tk.StringVar(options_frame)
    gorunurluk_var.set("Sadece Doktor")
    gorunurluk_menu = tk.OptionMenu(options_frame, gorunurluk_var, *gorunurluk_options)
    gorunurluk_menu.config(width=15)
    gorunurluk_menu.pack(side="left", padx=5)


    def save_doctor_note():
        title = note_title_entry.get().strip()
        content = note_content_text.get("1.0", tk.END).strip()
        onem_seviyesi = onem_seviyesi_var.get()
        gorunurluk = gorunurluk_var.get()

        if not title or not content:
            messagebox.showwarning("Uyarı", "Not başlığı ve içeriği boş bırakılamaz.", parent=parent_frame)
            return

        conn_save = connect_db()
        if not conn_save: return
        cursor_save = conn_save.cursor()
        try:
            cursor_save.execute("""
                INSERT INTO doktor_hasta_notlari (doktor_id, hasta_id, not_basligi, not_icerigi, onem_seviyesi, gorunurluk)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (current_user_doctor_id, hasta_id, title, content, onem_seviyesi, gorunurluk))
            conn_save.commit()
            messagebox.showinfo("Başarılı", "Not başarıyla kaydedildi!", parent=parent_frame)
            load_doctor_notes_for_patient(parent_frame, hasta_id) 
            note_title_entry.delete(0, tk.END)
            note_content_text.delete("1.0", tk.END)
        except Exception as e:
            conn_save.rollback()
            messagebox.showerror("Hata", f"Not kaydedilirken hata oluştu: {e}", parent=parent_frame)
        finally:
            if conn_save.is_connected():
                cursor_save.close()
                conn_save.close()

    tk.Button(parent_frame, text="Notu Kaydet", command=save_doctor_note,
              width=15, height=1, bg="darkblue", fg="white").pack(pady=10, anchor="e", padx=10)


def add_patient_screen(parent_window):
    add_patient_win = tk.Toplevel(parent_window)
    add_patient_win.title("Yeni Hasta Ekle")
    add_patient_win.geometry("500x650")

    fields = ["T.C. Kimlik No:", "Ad:", "Soyad:", "E-posta:", "Şifre:", "Doğum Tarihi (GG.AA.YYYY):"]
    entries = {}

    form_frame = tk.Frame(add_patient_win, padx=10, pady=10)
    form_frame.pack(fill="both", expand=True)

    for i, field in enumerate(fields):
        tk.Label(form_frame, text=field, font=("Arial", 10)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        entry = tk.Entry(form_frame, width=40)
        entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
        if "Şifre" in field:
             entry.config(show="*") 
        entries[field] = entry

    tk.Label(form_frame, text="Cinsiyet:", font=("Arial", 10)).grid(row=len(fields), column=0, padx=10, pady=5, sticky="w")
    cinsiyet_var = tk.StringVar(form_frame)
    cinsiyet_options = ["Erkek", "Kadın"]
    cinsiyet_var.set(cinsiyet_options[0])
    cinsiyet_menu = tk.OptionMenu(form_frame, cinsiyet_var, *cinsiyet_options)
    cinsiyet_menu.grid(row=len(fields), column=1, padx=10, pady=5, sticky="ew")

    tk.Label(form_frame, text="Diyabet Tipi:", font=("Arial", 10)).grid(row=len(fields)+1, column=0, padx=10, pady=5, sticky="w")
    diyabet_tipi_var = tk.StringVar(form_frame)
    diyabet_tipi_options = ["Tip 1", "Tip 2", "Gestasyonel"]
    diyabet_tipi_var.set(diyabet_tipi_options[1]) 
    diyabet_tipi_menu = tk.OptionMenu(form_frame, diyabet_tipi_var, *diyabet_tipi_options)
    diyabet_tipi_menu.grid(row=len(fields)+1, column=1, padx=10, pady=5, sticky="ew")

    tk.Label(form_frame, text="Tanı Tarihi (GG.AA.YYYY):", font=("Arial", 10)).grid(row=len(fields)+2, column=0, padx=10, pady=5, sticky="w")
    tani_tarihi_entry = tk.Entry(form_frame, width=40)
    tani_tarihi_entry.insert(0, datetime.date.today().strftime("%d.%m.%Y"))
    tani_tarihi_entry.grid(row=len(fields)+2, column=1, padx=10, pady=5, sticky="ew")
    
    tk.Label(form_frame, text="Hedef KS Min (mg/dL):", font=("Arial", 10)).grid(row=len(fields)+3, column=0, padx=10, pady=5, sticky="w")
    hedef_ks_min_entry = tk.Entry(form_frame, width=10)
    hedef_ks_min_entry.insert(0, "70")
    hedef_ks_min_entry.grid(row=len(fields)+3, column=1, padx=10, pady=5, sticky="w")

    tk.Label(form_frame, text="Hedef KS Max (mg/dL):", font=("Arial", 10)).grid(row=len(fields)+4, column=0, padx=10, pady=5, sticky="w")
    hedef_ks_max_entry = tk.Entry(form_frame, width=10)
    hedef_ks_max_entry.insert(0, "110")
    hedef_ks_max_entry.grid(row=len(fields)+4, column=1, padx=10, pady=5, sticky="w")


    def save_patient():
        tc_no = entries["T.C. Kimlik No:"].get().strip()
        ad = entries["Ad:"].get().strip()
        soyad = entries["Soyad:"].get().strip()
        eposta = entries["E-posta:"].get().strip()
        password_plain = entries["Şifre:"].get().strip() 
        dogum_tarihi_str = entries["Doğum Tarihi (GG.AA.YYYY):"].get().strip()
        cinsiyet = cinsiyet_var.get()
        diyabet_tipi = diyabet_tipi_var.get()
        tani_tarihi_str = tani_tarihi_entry.get().strip()
        hedef_min_str = hedef_ks_min_entry.get().strip()
        hedef_max_str = hedef_ks_max_entry.get().strip()


        if not all([tc_no, ad, soyad, eposta, password_plain, dogum_tarihi_str, cinsiyet, diyabet_tipi, tani_tarihi_str, hedef_min_str, hedef_max_str]):
            messagebox.showwarning("Giriş Hatası", "Tüm alanlar doldurulmalıdır!", parent=add_patient_win)
            return
        if not tc_no.isdigit() or len(tc_no) != 11:
            messagebox.showerror("Giriş Hatası", "T.C. Kimlik No 11 haneli sayı olmalıdır!", parent=add_patient_win)
            return
        if "@" not in eposta or "." not in eposta.split('@')[-1]:
            messagebox.showerror("Giriş Hatası", "Geçerli bir e-posta adresi girin.", parent=add_patient_win)
            return

        try:
            dogum_tarihi_db = datetime.datetime.strptime(dogum_tarihi_str, '%d.%m.%Y').date()
            tani_tarihi_db = datetime.datetime.strptime(tani_tarihi_str, '%d.%m.%Y').date()
            hedef_min = int(hedef_min_str)
            hedef_max = int(hedef_max_str)
            if hedef_min >= hedef_max:
                messagebox.showerror("Hata", "Hedef Min KS, Max KS'den küçük olmalıdır.", parent=add_patient_win)
                return
        except ValueError:
            messagebox.showerror("Giriş Hatası", "Tarih formatı GG.AA.YYYY, Hedef KS'ler sayı olmalıdır.", parent=add_patient_win)
            return
        
        conn = connect_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT kullanici_id FROM kullanicilar WHERE tc_kimlik_no = %s OR eposta = %s", (tc_no, eposta))
            if cursor.fetchone():
                messagebox.showerror("Hata", "Bu T.C. Kimlik No veya e-posta ile zaten bir kullanıcı mevcut.", parent=add_patient_win)
                conn.close()
                return

            cursor.execute("""
                INSERT INTO kullanicilar (tc_kimlik_no, ad, soyad, eposta, sifre, dogum_tarihi, cinsiyet, rol_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, (SELECT rol_id FROM kullanici_rolleri WHERE rol_adi = 'Hasta'))
            """, (tc_no, ad, soyad, eposta, password_plain, dogum_tarihi_db, cinsiyet))
            new_kullanici_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO hastalar (kullanici_id, doktor_id, diyabet_tipi, tani_tarihi, hedef_kan_sekeri_min, hedef_kan_sekeri_max)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (new_kullanici_id, current_user_doctor_id, diyabet_tipi, tani_tarihi_db, hedef_min, hedef_max))

            conn.commit()
            messagebox.showinfo("Başarılı", f"{ad} {soyad} adlı hasta başarıyla eklendi!", parent=add_patient_win)
            add_patient_win.destroy()
        except mysql.connector.Error as err:
            if err.errno == 1062:
                 messagebox.showerror("Hata", "Bu T.C. Kimlik No veya e-posta ile zaten bir kullanıcı mevcut.", parent=add_patient_win)
            else:
                messagebox.showerror("Veritabanı Hatası", f"Hasta eklenirken hata oluştu: {err}", parent=add_patient_win)
            conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Hasta eklenirken beklenmeyen bir hata oluştu: {e}", parent=add_patient_win)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(form_frame, text="Hasta Ekle", command=save_patient,
              width=20, height=2, bg="green", fg="white").grid(row=len(fields)+5, column=0, columnspan=2, pady=20)


def show_doctor_alerts(parent_window):
    alert_window = tk.Toplevel(parent_window)
    alert_window.title("Hasta Uyarıları (Doktor Ekranı)")
    alert_window.geometry("950x700")

    tk.Label(alert_window, text="Hastalarınıza Ait Okunmamış veya Kritik Uyarılar:",
             font=("Arial", 14, "bold")).pack(pady=10)

    controls_frame = tk.Frame(alert_window)
    controls_frame.pack(fill="x", padx=10)
    tk.Button(controls_frame, text="Listeyi Yenile", command=lambda: load_alerts_for_doctor(scrollable_alerts_frame, canvas_alerts, scrollbar_alerts)).pack(side="right", pady=5)


    alerts_frame = tk.Frame(alert_window)
    alerts_frame.pack(fill="both", expand=True, padx=10, pady=10)

    canvas_alerts = tk.Canvas(alerts_frame)
    scrollbar_alerts = tk.Scrollbar(alerts_frame, orient="vertical", command=canvas_alerts.yview)
    scrollable_alerts_frame = tk.Frame(canvas_alerts)

    scrollable_alerts_frame.bind(
        "<Configure>",
        lambda e: canvas_alerts.configure(scrollregion=canvas_alerts.bbox("all"))
    )
    canvas_alerts.create_window((0, 0), window=scrollable_alerts_frame, anchor="nw")
    canvas_alerts.configure(yscrollcommand=scrollbar_alerts.set)
    
    load_alerts_for_doctor(scrollable_alerts_frame, canvas_alerts, scrollbar_alerts)


def load_alerts_for_doctor(target_frame, target_canvas, target_scrollbar):
    for widget in target_frame.winfo_children():
        widget.destroy()
    
    conn = connect_db()
    if not conn: 
        tk.Label(target_frame, text="Veritabanı bağlantı hatası.").pack(pady=20)
        return
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
        SELECT
            u.uyari_id,
            CONCAT(hk.ad, ' ', hk.soyad) AS hasta_adi,
            hk.tc_kimlik_no AS hasta_tc,
            ut.uyari_adi,
            ut.aciliyet_seviyesi,
            u.uyari_mesaji,
            u.uyari_tarihi,
            u.kan_sekeri_degeri,
            u.okundu
        FROM uyarilar u
        JOIN hastalar h ON u.hasta_id = h.hasta_id
        JOIN kullanicilar hk ON h.kullanici_id = hk.kullanici_id
        JOIN uyari_turleri ut ON u.uyari_turu_id = ut.uyari_turu_id
        WHERE h.doktor_id = %s 
        ORDER BY u.okundu ASC, FIELD(ut.aciliyet_seviyesi, 'Kritik', 'Yüksek', 'Orta', 'Düşük') DESC, u.olusturma_tarihi DESC
        LIMIT 100
        """ 
        cursor.execute(query, (current_user_doctor_id,))
        alerts = cursor.fetchall()

        if alerts:
            for alert in alerts:
                bg_color = "lightcoral" if alert['aciliyet_seviyesi'] == 'Kritik' else \
                           "lightyellow" if not alert['okundu'] and alert['aciliyet_seviyesi'] == 'Yüksek' else \
                           "khaki1" if not alert['okundu'] and alert['aciliyet_seviyesi'] == 'Orta' else \
                           "lightgoldenrodyellow" if not alert['okundu'] else "lightgray"
                
                alert_item_frame = tk.LabelFrame(target_frame, 
                                                 text=f"Hasta: {alert['hasta_adi']} ({alert['hasta_tc']}) - {alert['uyari_adi']} ({alert['aciliyet_seviyesi']})",
                                                 font=("Arial", 10, "bold"), bg=bg_color, padx=5, pady=5)
                alert_item_frame.pack(fill="x", padx=5, pady=3)

                alert_text = (f"Mesaj: {alert['uyari_mesaji']}\n"
                              f"Uyarı Tarihi: {alert['uyari_tarihi'].strftime('%d.%m.%Y')}\n"
                              f"İlgili Kan Şekeri: {alert['kan_sekeri_degeri'] if alert['kan_sekeri_degeri'] else 'N/A'} mg/dL\n"
                              f"Durum: {'Okundu' if alert['okundu'] else 'Okunmadı'}")
                tk.Label(alert_item_frame, text=alert_text, justify=tk.LEFT, font=("Arial", 9), bg=bg_color, anchor="w", wraplength=800).pack(anchor="w", fill="x")

                if not alert['okundu']:
                    def mark_as_read_action(alert_id_to_mark=alert['uyari_id'], frame=target_frame, canv=target_canvas, scrollb=target_scrollbar):
                        if messagebox.askyesno("Okundu İşaretle", "Bu uyarıyı okundu olarak işaretlemek istediğinizden emin misiniz?", parent=frame.winfo_toplevel()):
                            update_alert_status_for_uyarilar(alert_id_to_mark, True)
                            load_alerts_for_doctor(frame, canv, scrollb) 

                    tk.Button(alert_item_frame, text="Okundu İşaretle",
                              command=mark_as_read_action, bg="skyblue", font=("Arial", 8)).pack(anchor="e", pady=2)
        else:
            tk.Label(target_frame, text="Şu anda okunmamış veya kritik uyarı yok.",
                     font=("Arial", 12)).pack(pady=50)
    
    except mysql.connector.Error as db_err:
        messagebox.showerror("Sorgu Hatası", f"Uyarıları çekerken hata oluştu: {db_err}", parent=target_frame.winfo_toplevel())
    except Exception as e:
        messagebox.showerror("Genel Hata", f"Uyarıları yüklerken hata: {e}", parent=target_frame.winfo_toplevel())
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
    target_canvas.pack(side="left", fill="both", expand=True)
    target_scrollbar.pack(side="right", fill="y")


def update_alert_status_for_uyarilar(alert_id, status_bool): 
    conn_update = connect_db()
    if not conn_update: return False
    cursor_update = conn_update.cursor()
    updated = False
    try:
        query = "UPDATE uyarilar SET okundu = %s WHERE uyari_id = %s"
        cursor_update.execute(query, (status_bool, alert_id))
        conn_update.commit()
        if cursor_update.rowcount > 0:
            updated = True
    except Exception as e:
        messagebox.showerror("Hata", f"Uyarı durumu güncellenirken hata oluştu: {e}")
        conn_update.rollback()
    finally:
        if conn_update.is_connected():
            cursor_update.close()
            conn_update.close()
    return updated

def show_critical_patients(parent_window):
    critical_window = tk.Toplevel(parent_window)
    critical_window.title("Kritik Durumdaki Hastalar")
    critical_window.geometry("850x600")

    tk.Label(critical_window, text="Kritik Durumdaki Hastalarınız (View: kritik_hastalar):", font=("Arial", 14, "bold")).pack(pady=10)

    conn = connect_db()
    if not conn: return
    cursor = conn.cursor(dictionary=True)
    
    list_frame = tk.Frame(critical_window)
    list_frame.pack(fill="both", expand=True, padx=10, pady=10)

    canvas = tk.Canvas(list_frame)
    scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    try:
        query = """
        SELECT * FROM kritik_hastalar WHERE doktor_id = %s
        ORDER BY FIELD(durum_kategorisi, 'Kritik Durum (Kan Şekeri)', 'Ölçüm Eksikliği', 'Düşük Uyum', 'Stabil'), son_7_gun_ortalama_kan_sekeri DESC
        """
        cursor.execute(query, (current_user_doctor_id,))
        critical_patients = cursor.fetchall()

        if critical_patients:
            for patient in critical_patients:
                bg_color = "red" if "Kan Şekeri" in patient['durum_kategorisi'] else \
                           "orange" if "Eksikliği" in patient['durum_kategorisi'] or "Düşük Uyum" in patient['durum_kategorisi'] else \
                           "lightsalmon" 
                
                patient_frame = tk.LabelFrame(scrollable_frame, text=f"{patient['hasta_adi']} - Durum: {patient['durum_kategorisi']}",
                                              font=("Arial", 11, "bold"), padx=10, pady=5, bg=bg_color, fg="black" if bg_color != "red" else "white")
                patient_frame.pack(fill="x", padx=10, pady=5)

                details_text = (f"  Ort. KS (Son 7 Gün): {patient['son_7_gun_ortalama_kan_sekeri']:.1f} mg/dL\n"
                                f"  Ölçüm Gün Sayısı (Son 7 Gün): {patient['son_7_gun_olcum_gun_sayisi']}\n"
                                f"  Kritik Uyarı Sayısı (Son 7 Gün): {patient.get('kritik_uyari_sayisi', 0)}\n" 
                                f"  Son Uyum Skoru (%): {patient['son_uyum_skoru']:.1f}")
                tk.Label(patient_frame, text=details_text, anchor="w", bg=bg_color, fg="black" if bg_color != "red" else "white", justify=tk.LEFT).pack(fill="x")

                tk.Button(patient_frame, text="Detayları Görüntüle",
                          command=lambda p_id=patient['hasta_id']: show_patient_details_for_doctor(critical_window, p_id),
                          width=20, bg="lightblue").pack(pady=5, anchor="e")
        else:
            tk.Label(scrollable_frame, text="Şu anda kritik durumda olan hastanız bulunmamaktadır.", font=("Arial", 12)).pack(pady=50)

    except mysql.connector.Error as db_err:
         messagebox.showerror("Veritabanı Hatası", f"Kritik hastaları çekerken hata oluştu: {db_err}", parent=critical_window)
    except Exception as e:
        messagebox.showerror("Hata", f"Kritik hastaları çekerken hata oluştu: {e}", parent=critical_window)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def show_patient_report_options(parent_window):
    report_win = tk.Toplevel(parent_window)
    report_win.title("Hasta Raporu Oluştur")
    report_win.geometry("500x350")

    tk.Label(report_win, text="Rapor Oluşturmak İçin Hasta Seçin ve Tarih Aralığı Girin", font=("Arial", 12, "bold")).pack(pady=10)

    conn = connect_db()
    if not conn: return
    cursor = conn.cursor(dictionary=True) 
    patients_data = []
    patient_names_map = {} 
    try:
        cursor.execute("""
            SELECT h.hasta_id, k.ad, k.soyad, k.tc_kimlik_no
            FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
            WHERE h.doktor_id = %s
            ORDER BY k.ad, k.soyad
        """, (current_user_doctor_id,))
        patients_data = cursor.fetchall()
        patient_names = [f"{p['ad']} {p['soyad']} (TC: {p.get('tc_kimlik_no', 'N/A')})" for p in patients_data]
        patient_names_map = {f"{p['ad']} {p['soyad']} (TC: {p.get('tc_kimlik_no', 'N/A')})": p['hasta_id'] for p in patients_data}


    except Exception as e:
        messagebox.showerror("Hata", f"Hasta listesi alınırken hata: {e}", parent=report_win)
        report_win.destroy()
        return
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    if not patient_names:
        tk.Label(report_win, text="Rapor oluşturulacak hasta bulunamadı.").pack(pady=50)
        return

    selected_patient_var = tk.StringVar(report_win)
    if patient_names: selected_patient_var.set(patient_names[0])

    tk.Label(report_win, text="Hasta:", font=("Arial", 10)).pack(pady=(10,2))
    patient_menu = tk.OptionMenu(report_win, selected_patient_var, *patient_names)
    patient_menu.config(width=40)
    patient_menu.pack(pady=5)

    tk.Label(report_win, text="Başlangıç Tarihi:", font=("Arial", 10)).pack(pady=(10,2))
    start_date_entry = DateEntry(report_win, width=18, date_pattern='dd.mm.yyyy')
    start_date_entry.set_date(datetime.date.today() - datetime.timedelta(days=30))
    start_date_entry.pack(pady=5)

    tk.Label(report_win, text="Bitiş Tarihi:", font=("Arial", 10)).pack(pady=(10,2))
    end_date_entry = DateEntry(report_win, width=18,date_pattern='dd.mm.yyyy')
    end_date_entry.set_date(datetime.date.today())
    end_date_entry.pack(pady=5)

    def generate_report():
        selected_name_full = selected_patient_var.get()
        hasta_id_to_report = patient_names_map.get(selected_name_full)

        if not hasta_id_to_report:
            messagebox.showerror("Hata", "Hasta seçimi geçersiz.", parent=report_win)
            return

        try:
            start_date = start_date_entry.get_date()
            end_date = end_date_entry.get_date()
            if start_date > end_date:
                messagebox.showerror("Hata", "Başlangıç tarihi bitiş tarihinden sonra olamaz.", parent=report_win)
                return
        except Exception:
            messagebox.showerror("Hata", "Lütfen geçerli tarihler girin.", parent=report_win)
            return

        display_patient_report(report_win, hasta_id_to_report, start_date, end_date)

    tk.Button(report_win, text="Rapor Oluştur", command=generate_report,
              width=20, height=2, bg="blue", fg="white").pack(pady=20)


def display_patient_report(parent_window, hasta_id, start_date_dt, end_date_dt):
    report_display_win = tk.Toplevel(parent_window)
    report_display_win.title("Hasta Raporu")
    report_display_win.geometry("850x700")

    text_area = scrolledtext.ScrolledText(report_display_win, wrap=tk.WORD, width=100, height=40, font=("Courier New", 9)) 
    text_area.pack(pady=10, padx=10, fill="both", expand=True)
    
    start_date_str_db = start_date_dt.strftime('%Y-%m-%d')
    end_date_str_db = end_date_dt.strftime('%Y-%m-%d')

    text_area.insert(tk.END, f"--- HASTA RAPORU ({start_date_dt.strftime('%d.%m.%Y')} - {end_date_dt.strftime('%d.%m.%Y')}) ---\n\n")

    conn = connect_db()
    if not conn: 
        text_area.insert(tk.END, "Veritabanı bağlantı hatası.\n")
        text_area.config(state=tk.DISABLED)
        return

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.callproc('hasta_rapor_olustur', [hasta_id, start_date_str_db, end_date_str_db])
        report_sections = []
        for result in cursor.stored_results():
            report_sections.extend(result.fetchall())

        if report_sections:
            for section in report_sections:
                text_area.insert(tk.END, f"### {section['bolum'].upper()} ###\n", ("bold_underline",))
                
                veri_json_str = section.get('veri')
                if veri_json_str:
                    try:
                        veri_dict = json.loads(veri_json_str) if isinstance(veri_json_str, str) else veri_json_str 
                        for key, value in veri_dict.items():
                            key_tr = key.replace('_', ' ').capitalize()
                            if isinstance(value, dict) and 'baslangic' in value and 'bitis' in value: 
                                value_str = f"Başlangıç: {datetime.datetime.strptime(value['baslangic'], '%Y-%m-%d').strftime('%d.%m.%Y')}, Bitiş: {datetime.datetime.strptime(value['bitis'], '%Y-%m-%d').strftime('%d.%m.%Y')}"
                            elif key.endswith('_tarihi') and isinstance(value, str) and '-' in value and 'T' not in value : 
                                try:
                                    value_str = datetime.datetime.strptime(value.split('T')[0], '%Y-%m-%d').strftime('%d.%m.%Y')
                                except ValueError:
                                    value_str = value 
                            else:
                                value_str = f"{value:.2f}" if isinstance(value, float) else value
                            text_area.insert(tk.END, f"  {key_tr:<30}: {value_str}\n")
                    except json.JSONDecodeError:
                         text_area.insert(tk.END, f"  Veri (JSON değil): {veri_json_str}\n") 
                else:
                    text_area.insert(tk.END, "  Bu bölüm için veri bulunamadı.\n")
                text_area.insert(tk.END, "\n")
        else:
            text_area.insert(tk.END, "Seçilen tarih aralığı için rapor verisi bulunamadı.")
    except Exception as e:
        messagebox.showerror("Hata", f"Rapor oluşturulurken hata oluştu: {e}", parent=report_display_win)
        text_area.insert(tk.END, f"Rapor oluşturulurken bir hata meydana geldi: {e}\n")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    
    text_area.tag_configure("bold_underline", font=("Courier New", 10, "bold", "underline"))
    text_area.config(state=tk.DISABLED)


def enter_blood_sugar(parent_window, user_kullanici_id):
    bs_window = tk.Toplevel(parent_window)
    bs_window.title("Kan Şekeri Ölçümü Gir")
    bs_window.geometry("450x400") 

    tk.Label(bs_window, text="Kan Şekeri Değeri (mg/dL):", font=("Arial", 12)).pack(pady=10)
    bs_value_entry = tk.Entry(bs_window, width=20, font=("Arial", 11))
    bs_value_entry.pack(pady=5)
    bs_value_entry.focus_set()

    tk.Label(bs_window, text="Ölçüm Tipi:", font=("Arial", 12)).pack(pady=(15, 5))
    olcum_tipleri = ['Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece', 'Diğer']
    bs_type_var = tk.StringVar(bs_window)
    bs_type_var.set('Sabah')
    bs_type_option = tk.OptionMenu(bs_window, bs_type_var, *olcum_tipleri)
    bs_type_option.config(width=15)
    bs_type_option.pack(pady=5)

    info_text = """Önerilen Ölçüm Saatleri:
• Sabah: 07:00 - 08:59 (07-08 PDF) [cite: 25]
• Öğle: 12:00 - 13:59 (12-13 PDF) [cite: 26]
• İkindi: 15:00 - 16:59 (15-16 PDF) [cite: 27]
• Akşam: 18:00 - 19:59 (18-19 PDF) [cite: 28]
• Gece: 22:00 - 23:59 (22-23 PDF) [cite: 29]
Saat dışı girişler kaydedilir ancak insülin öneri ortalamasına DAHİL EDİLMEZ. [cite: 41]"""

    tk.Label(bs_window, text=info_text, font=("Arial", 9),
             justify=tk.LEFT, fg="blue").pack(pady=10)

    def save_blood_sugar():
        global current_patient_id 
        if current_patient_id is None:
            messagebox.showerror("Hata", "Hasta ID bulunamadı. Lütfen tekrar giriş yapın.", parent=bs_window)
            return

        value_str = bs_value_entry.get().strip()
        olcum_tipi = bs_type_var.get()

        if not value_str:
            messagebox.showwarning("Giriş Hatası", "Kan Şekeri Değeri boş bırakılamaz.", parent=bs_window)
            return

        try:
            value = float(value_str)
            if not (0 <= value <= 1000): 
                messagebox.showerror("Hata", "Kan şekeri değeri 0 ile 1000 arasında olmalıdır.", parent=bs_window)
                return
        except ValueError:
            messagebox.showerror("Hata", "Kan şekeri değeri sayı olmalıdır.", parent=bs_window)
            return

        current_datetime = datetime.datetime.now()
        olcum_tarihi_db = current_datetime.date()
        olcum_saati_db = current_datetime.time()
        olcum_zamani_db = current_datetime 

        gecerli_olcum_db_icin = True 
        saat = current_datetime.hour
        user_warning_message = ""

        if olcum_tipi == 'Sabah' and not (7 <= saat < 9): gecerli_olcum_db_icin = True
        elif olcum_tipi == 'Öğle' and not (12 <= saat < 14): gecerli_olcum_db_icin = True
        elif olcum_tipi == 'İkindi' and not (15 <= saat < 17): gecerli_olcum_db_icin = True
        elif olcum_tipi == 'Akşam' and not (18 <= saat < 20): gecerli_olcum_db_icin = True
        elif olcum_tipi == 'Gece' and not (22 <= saat <= 23): gecerli_olcum_db_icin = True
        
        if not gecerli_olcum_db_icin and olcum_tipi != 'Diğer':
            user_warning_message = (f"Ölçümünüz ({value} mg/dL) kaydedildi.\n"
                                    f"Ancak, {olcum_tipi} ölçümü için önerilen saat aralığı dışındadır.\n"
                                    f"Bu ölçüm, insülin önerisi ortalamasına DAHİL EDİLMEYECEKTİR.\n"
                                    f"Lütfen ölçümlerinizi belirtilen saatlerde yapmaya özen gösterin.") 
        
        conn = connect_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            query_insert_bs = """
                INSERT INTO kan_sekeri_olcumleri 
                (hasta_id, olcum_tarihi, olcum_saati, olcum_zamani, kan_sekeri_degeri, olcum_tipi, gecerli_olcum)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_insert_bs, (current_patient_id, olcum_tarihi_db, olcum_saati_db, olcum_zamani_db, value, olcum_tipi, gecerli_olcum_db_icin))
            
            if user_warning_message:
                messagebox.showwarning("Saat Uyarısı", user_warning_message, parent=bs_window)
            else:
                 messagebox.showinfo("Başarılı", "Kan şekeri ölçümü başarıyla kaydedildi!", parent=bs_window)
            
            conn.commit()
            
            try:
                cursor.callproc('insulin_onerisi_olustur', [current_patient_id, olcum_tarihi_db, olcum_tipi])
                conn.commit() 
            except Exception as proc_err:
                print(f"İnsülin önerisi oluşturulurken hata: {proc_err}")
            
            bs_window.destroy()

        except mysql.connector.Error as db_err:
            conn.rollback()
            messagebox.showerror("Veritabanı Hatası", f"Ölçüm kaydedilirken hata oluştu: {db_err}", parent=bs_window)
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Hata", f"Ölçüm kaydedilirken beklenmeyen bir hata oluştu: {e}", parent=bs_window)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    tk.Button(bs_window, text="Kaydet", command=save_blood_sugar,
              width=15, height=2, bg="green", fg="white").pack(pady=20)
    bs_window.bind('<Return>', lambda event: save_blood_sugar())


def enter_diet_exercise(parent_window, user_kullanici_id):
    de_window = tk.Toplevel(parent_window)
    de_window.title("Diyet ve Egzersiz Durumu Gir")
    de_window.geometry("400x400")

    if current_patient_id is None:
        messagebox.showerror("Hata", "Hasta kaydı bulunamadı.", parent=de_window)
        de_window.destroy()
        return

    diyet_frame = tk.LabelFrame(de_window, text="Diyet Durumu", font=("Arial", 12))
    diyet_frame.pack(pady=10, padx=20, fill="x")

    diyet_var = tk.BooleanVar()
    tk.Checkbutton(diyet_frame, text="Bugün diyetimi uyguladım",
                  variable=diyet_var, font=("Arial", 10)).pack(pady=10)

    egzersiz_frame = tk.LabelFrame(de_window, text="Egzersiz Durumu", font=("Arial", 12))
    egzersiz_frame.pack(pady=10, padx=20, fill="x")

    egzersiz_var = tk.BooleanVar()
    tk.Checkbutton(egzersiz_frame, text="Bugün egzersiz yaptım",
                  variable=egzersiz_var, font=("Arial", 10)).pack(pady=5)

    tk.Label(egzersiz_frame, text="Egzersiz Süresi (dakika - opsiyonel):",
             font=("Arial", 10)).pack(pady=(10, 5))
    sure_entry = tk.Entry(egzersiz_frame, width=15)
    sure_entry.pack(pady=5)

    tk.Label(de_window, text=f"Tarih: {datetime.date.today().strftime('%d.%m.%Y')}",
             font=("Arial", 10), fg="gray").pack(pady=10)

    def save_diet_exercise():
        diyet_uygulandimi = diyet_var.get()
        egzersiz_yapildimi = egzersiz_var.get()
        sure_str = sure_entry.get().strip()
        takip_tarihi_db = datetime.date.today().strftime("%Y-%m-%d")

        sure_db = None
        if egzersiz_yapildimi:
            if sure_str:
                try:
                    sure_db = int(sure_str)
                    if sure_db < 0:
                        messagebox.showerror("Hata", "Egzersiz süresi negatif olamaz.", parent=de_window)
                        return
                except ValueError:
                    messagebox.showerror("Hata", "Egzersiz süresi sayı olmalıdır.", parent=de_window)
                    return
        
        conn = connect_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            query_diyet = """
                INSERT INTO diyet_takibi (hasta_id, takip_tarihi, diyet_uygulandimi)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE diyet_uygulandimi = VALUES(diyet_uygulandimi)
            """
            cursor.execute(query_diyet, (current_patient_id, takip_tarihi_db, diyet_uygulandimi))

            query_egzersiz = """
                INSERT INTO egzersiz_takibi (hasta_id, takip_tarihi, egzersiz_yapildimi, sure_dakika)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE egzersiz_yapildimi = VALUES(egzersiz_yapildimi), sure_dakika = VALUES(sure_dakika)
            """
            cursor.execute(query_egzersiz, (current_patient_id, takip_tarihi_db, egzersiz_yapildimi, sure_db))

            conn.commit()
            messagebox.showinfo("Başarılı", "Diyet ve Egzersiz durumu başarıyla kaydedildi!", parent=de_window)
            de_window.destroy()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Hata", f"Diyet/Egzersiz durumu kaydedilirken hata oluştu: {e}", parent=de_window)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    tk.Button(de_window, text="Kaydet", command=save_diet_exercise,
              width=15, height=2, bg="green", fg="white").pack(pady=20)

def get_symptom_options():
    conn = connect_db()
    if not conn: return []
    cursor = conn.cursor()
    symptoms_data = []
    try:
        cursor.execute("SELECT belirti_id, belirti_adi FROM belirtiler ORDER BY belirti_adi")
        symptoms_data = cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Hata", f"Semptomlar yüklenirken hata oluştu: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return symptoms_data


def enter_symptoms(parent_window, user_kullanici_id):
    sym_window = tk.Toplevel(parent_window)
    sym_window.title("Semptom Takibi (Hasta)")
    sym_window.geometry("500x550")

    if current_patient_id is None:
        messagebox.showerror("Hata", "Hasta kaydı bulunamadı.", parent=sym_window)
        sym_window.destroy()
        return

    tk.Label(sym_window, text="Bugün Hangi Semptomları Yaşadınız?", font=("Arial", 12, "bold")).pack(pady=10)

    symptoms_options = get_symptom_options()
    if not symptoms_options:
        tk.Label(sym_window, text="Sistemde tanımlı semptom bulunmamaktadır.", fg="red").pack(pady=20)
        return

    symptom_vars = {}
    symptoms_check_frame = tk.Frame(sym_window)
    symptoms_check_frame.pack(pady=10, fill="x", padx=20)

    for i, (s_id, s_name) in enumerate(symptoms_options):
        var = tk.BooleanVar()
        cb = tk.Checkbutton(symptoms_check_frame, text=s_name, variable=var, font=("Arial", 10))
        cb.pack(anchor="w")
        symptom_vars[s_id] = var

    tk.Label(sym_window, text="Semptom Şiddeti (Tümü için ortak):", font=("Arial", 10)).pack(pady=(10,2))
    siddet_var = tk.StringVar(sym_window)
    siddet_options = ["Hafif", "Orta", "Şiddetli"]
    siddet_var.set("Orta")
    siddet_menu = tk.OptionMenu(sym_window, siddet_var, *siddet_options)
    siddet_menu.pack(pady=5)

    tk.Label(sym_window, text="Ek Notlar (Opsiyonel):", font=("Arial", 10)).pack(pady=(10,2))
    notes_entry = tk.Entry(sym_window, width=50)
    notes_entry.pack(pady=5, padx=20)

    def save_symptoms():
        kayit_tarihi_db = datetime.date.today().strftime("%Y-%m-%d")
        notes = notes_entry.get().strip()
        siddet = siddet_var.get()

        selected_s_ids = [s_id for s_id, var_ in symptom_vars.items() if var_.get()]

        if not selected_s_ids:
            messagebox.showwarning("Giriş Hatası", "En az bir semptom seçmelisiniz.", parent=sym_window)
            return

        conn = connect_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            for s_id in selected_s_ids:
                query = """
                    INSERT INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi, siddet_seviyesi, notlar, doktor_id)
                    VALUES (%s, %s, %s, %s, %s, NULL)
                    ON DUPLICATE KEY UPDATE siddet_seviyesi = VALUES(siddet_seviyesi), notlar = VALUES(notlar), doktor_id = NULL 
                """ 
                cursor.execute(query, (current_patient_id, s_id, kayit_tarihi_db, siddet, notes))
            conn.commit()
            messagebox.showinfo("Başarılı", "Semptomlar başarıyla kaydedildi!", parent=sym_window)
            sym_window.destroy()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Hata", f"Semptomlar kaydedilirken hata oluştu: {e}", parent=sym_window)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    tk.Button(sym_window, text="Semptomları Kaydet", command=save_symptoms,
              width=20, height=2, bg="green", fg="white").pack(pady=20)

def show_blood_sugar_history_and_graphs(parent_window, user_kullanici_id):
    history_window = tk.Toplevel(parent_window)
    history_window.title("Kan Şekeri Geçmişi, Ortalaması ve Grafikler")
    history_window.geometry("950x750") 

    if current_patient_id is None:
        messagebox.showerror("Hata", "Hasta kaydı bulunamadı.", parent=history_window)
        history_window.destroy()
        return

    tk.Label(history_window, text="Kan Şekeri Ölçüm Geçmişi", font=("Arial", 14, "bold")).pack(pady=10)
    
    avg_frame = tk.Frame(history_window)
    avg_frame.pack(pady=5, fill="x", padx=10)
    tk.Label(avg_frame, text="Tarih Seçin (Günlük Ortalama İçin):", font=("Arial", 10)).pack(side="left", padx=5)
    avg_date_entry = DateEntry(avg_frame, width=12, date_pattern='dd.mm.yyyy')
    avg_date_entry.set_date(datetime.date.today())
    avg_date_entry.pack(side="left", padx=5)
    avg_display_label = tk.Label(avg_frame, text="Ortalama: -", font=("Arial", 10, "bold"))
    avg_display_label.pack(side="left", padx=10)

    def display_daily_average(event=None): 
        selected_date_dt = avg_date_entry.get_date()
        selected_date_str = selected_date_dt.strftime("%Y-%m-%d")
        conn_avg = connect_db()
        if not conn_avg: 
            avg_display_label.config(text="Ortalama: Bağlantı Yok")
            return
        cursor_avg = conn_avg.cursor(dictionary=True)
        try:
            cursor_avg.execute("SELECT gunluk_ortalama_hesapla(%s, %s) AS gunluk_ortalama", (current_patient_id, selected_date_str))
            result = cursor_avg.fetchone()
            if result and result['gunluk_ortalama'] is not None and float(result['gunluk_ortalama']) > 0:
                avg_display_label.config(text=f"Ortalama ({selected_date_dt.strftime('%d.%m.%Y')}): {float(result['gunluk_ortalama']):.2f} mg/dL")
            else:
                avg_display_label.config(text=f"Ortalama ({selected_date_dt.strftime('%d.%m.%Y')}): Veri Yok")
        except Exception as e:
            avg_display_label.config(text="Ortalama Hesaplanamadı")
            print(f"Error calculating daily average: {e}")
        finally:
            if conn_avg.is_connected():
                cursor_avg.close()
                conn_avg.close()
    
    avg_date_entry.bind("<<DateEntrySelected>>", display_daily_average)
    tk.Button(avg_frame, text="Ortalamayı Göster", command=display_daily_average).pack(side="left", padx=5)


    text_area = scrolledtext.ScrolledText(history_window, wrap=tk.WORD, width=90, height=10, font=("Arial", 10))
    text_area.pack(pady=5, padx=10, fill="x")
    text_area.insert(tk.END, "Son Kan Şekeri Ölçümleriniz (En Yeni Üstte):\n")

    conn = connect_db()
    if not conn: 
        text_area.insert(tk.END, "Veritabanı bağlantı hatası.")
        text_area.config(state=tk.DISABLED)
    else:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT olcum_tarihi, olcum_saati, kan_sekeri_degeri, olcum_tipi, gecerli_olcum
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = %s
                ORDER BY olcum_tarihi DESC, olcum_saati DESC
                LIMIT 50 
            """, (current_patient_id,))
            measurements = cursor.fetchall()

            if measurements:
                for m in measurements:
                    valid_status = "Geçerli (Ort. Dahil)" if m['gecerli_olcum'] else "Saat Dışı (Ort. Hariç)"
                    text_area.insert(tk.END, f"{m['olcum_tarihi'].strftime('%d.%m.%Y')} {m['olcum_saati'].strftime('%H:%M')} - {m['olcum_tipi']}: {m['kan_sekeri_degeri']} mg/dL ({valid_status})\n")
            else:
                text_area.insert(tk.END, "Henüz kan şekeri ölçümü bulunmamaktadır.")
            text_area.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Hata", f"Kan şekeri geçmişi yüklenirken hata oluştu: {e}", parent=history_window)
        finally:
            if conn.is_connected(): 
                cursor.close()
                conn.close()
    
    display_daily_average() 

    tk.Label(history_window, text="Kan Şekeri Değişim Grafiği", font=("Arial", 12, "bold")).pack(pady=(15,5))
    plot_blood_sugar_trend(history_window, current_patient_id) 


def show_patient_compliance(parent_window, user_kullanici_id):
    compliance_window = tk.Toplevel(parent_window)
    compliance_window.title("Diyet ve Egzersiz Uyum Takibi (%)")
    compliance_window.geometry("900x650") 

    if current_patient_id is None:
        messagebox.showerror("Hata", "Hasta kaydı bulunamadı.", parent=compliance_window)
        compliance_window.destroy()
        return

    tk.Label(compliance_window, text="Diyet, Egzersiz ve Ölçüm Uyum Raporunuz (%)", font=("Arial", 14, "bold")).pack(pady=10)
    plot_compliance_percentages(compliance_window, current_patient_id, "Hasta")

    tk.Label(compliance_window, text="Son 7 Günlük Detaylı Uyum Verileri:", font=("Arial", 12, "bold")).pack(pady=10)
    text_area_compliance = scrolledtext.ScrolledText(compliance_window, wrap=tk.WORD, width=80, height=10, font=("Arial", 10))
    text_area_compliance.pack(pady=5, padx=10, fill="x")

    conn = connect_db()
    if not conn: 
        text_area_compliance.insert(tk.END, "Veritabanı bağlantı hatası.")
        text_area_compliance.config(state=tk.DISABLED)
        return

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT hesaplama_tarihi, diyet_uyum_orani, egzersiz_uyum_orani, olcum_uyum_orani, genel_uyum_skoru
            FROM hasta_uyum_skorlari
            WHERE hasta_id = %s
            ORDER BY hesaplama_tarihi DESC
            LIMIT 7 
        """, (current_patient_id,))
        compliance_data = cursor.fetchall()

        if compliance_data:
            for data_row in compliance_data:
                text_area_compliance.insert(tk.END, f"Tarih: {data_row['hesaplama_tarihi'].strftime('%d.%m.%Y')}\n")
                text_area_compliance.insert(tk.END, f"  Diyet Uyumu: {data_row['diyet_uyum_orani']:.1f}%\n")
                text_area_compliance.insert(tk.END, f"  Egzersiz Uyumu: {data_row['egzersiz_uyum_orani']:.1f}%\n")
                text_area_compliance.insert(tk.END, f"  Ölçüm Uyumu: {data_row['olcum_uyum_orani']:.1f}%\n")
                text_area_compliance.insert(tk.END, f"  Genel Uyum Skoru: {data_row['genel_uyum_skoru']:.1f}%\n\n")
        else:
            text_area_compliance.insert(tk.END, "Henüz uyum skoru verisi bulunmamaktadır.")
        text_area_compliance.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Hata", f"Uyum verileri yüklenirken hata oluştu: {e}", parent=compliance_window)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def show_insulin_recommendations_for_patient_filtered(parent_window, user_kullanici_id):
    ins_window = tk.Toplevel(parent_window)
    ins_window.title("İnsülin Önerilerim (Filtreli)")
    ins_window.geometry("750x600") 

    if current_patient_id is None:
        messagebox.showerror("Hata", "Hasta kaydı bulunamadı.", parent=ins_window)
        ins_window.destroy()
        return

    tk.Label(ins_window, text="İnsülin Önerileriniz:", font=("Arial", 14, "bold")).pack(pady=10)

    filter_frame_ins = tk.Frame(ins_window)
    filter_frame_ins.pack(pady=5, fill="x", padx=10)
    
    tk.Label(filter_frame_ins, text="Başlangıç Tarihi:", font=("Arial", 10)).pack(side="left")
    start_date_entry_ins = DateEntry(filter_frame_ins, width=12, date_pattern='dd.mm.yyyy', locale='tr_TR')
    start_date_entry_ins.set_date(datetime.date.today() - datetime.timedelta(days=30)) 
    start_date_entry_ins.pack(side="left", padx=5)

    tk.Label(filter_frame_ins, text="Bitiş Tarihi:", font=("Arial", 10)).pack(side="left")
    end_date_entry_ins = DateEntry(filter_frame_ins, width=12,date_pattern='dd.mm.yyyy', locale='tr_TR')
    end_date_entry_ins.set_date(datetime.date.today())
    end_date_entry_ins.pack(side="left", padx=5)
    
    results_frame = tk.Frame(ins_window)
    results_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    canvas_ins = tk.Canvas(results_frame)
    scrollbar_ins = tk.Scrollbar(results_frame, orient="vertical", command=canvas_ins.yview)
    scrollable_frame_ins = tk.Frame(canvas_ins)
    scrollable_frame_ins.bind("<Configure>", lambda e: canvas_ins.configure(scrollregion=canvas_ins.bbox("all")))
    canvas_ins.create_window((0,0), window=scrollable_frame_ins, anchor="nw")
    canvas_ins.configure(yscrollcommand=scrollbar_ins.set)


    def load_filtered_insulin_recommendations():
        for widget in scrollable_frame_ins.winfo_children():
            widget.destroy()
        
        try:
            start_date_val = start_date_entry_ins.get_date()
            end_date_val = end_date_entry_ins.get_date()
            if start_date_val > end_date_val:
                messagebox.showerror("Hata", "Başlangıç tarihi bitiş tarihinden sonra olamaz.", parent=ins_window)
                return
        except Exception:
            messagebox.showerror("Hata", "Lütfen geçerli tarih aralığı girin.", parent=ins_window)
            return

        conn = connect_db()
        if not conn: 
            tk.Label(scrollable_frame_ins, text="Veritabanı bağlantı hatası.").pack(pady=20)
            return

        cursor = conn.cursor(dictionary=True)
        try:
            query = """
                SELECT oneri_id, tarih, olcum_tipi, ortalama_kan_sekeri, onerilen_doz_ml, uygulandi
                FROM insulin_onerileri
                WHERE hasta_id = %s AND tarih BETWEEN %s AND %s
                ORDER BY tarih DESC, FIELD(olcum_tipi, 'Gece', 'Akşam', 'İkindi', 'Öğle', 'Sabah') DESC
            """
            cursor.execute(query, (current_patient_id, start_date_val.strftime('%Y-%m-%d'), end_date_val.strftime('%Y-%m-%d')))
            recommendations = cursor.fetchall()

            if recommendations:
                for i, rec in enumerate(recommendations):
                    status = "✓ Uyguladım" if rec['uygulandi'] else "⏳ Uygulamadım"
                    rec_text = (f"{i+1}. Tarih: {rec['tarih'].strftime('%d.%m.%Y')} - {rec['olcum_tipi']}\n"
                                f"    Ortalama KS: {rec['ortalama_kan_sekeri']:.1f} mg/dL\n"
                                f"    Önerilen Doz: {rec['onerilen_doz_ml']:.1f} ml\n"
                                f"    Durum: {status}")

                    rec_frame = tk.Frame(scrollable_frame_ins, relief="ridge", bd=1, padx=5, pady=2)
                    rec_frame.pack(fill="x", pady=3)
                    tk.Label(rec_frame, text=rec_text, justify=tk.LEFT, font=("Arial", 9), anchor="w").pack(side="left", anchor="w")

                    if not rec['uygulandi']:
                        tk.Button(rec_frame, text="Uyguladım İşaretle",
                                  command=lambda r_id=rec['oneri_id']: confirm_and_mark_insulin_applied_by_patient(r_id, load_filtered_insulin_recommendations),
                                  bg="lightgreen", font=("Arial", 8)).pack(side="right", padx=5)
            else:
                tk.Label(scrollable_frame_ins, text="Belirtilen tarih aralığında insülin öneriniz bulunmuyor.",
                         font=("Arial", 11)).pack(pady=30)
            
            canvas_ins.pack(side="left", fill="both", expand=True)
            scrollbar_ins.pack(side="right", fill="y")

        except Exception as e:
            messagebox.showerror("Sorgu Hatası", f"İnsülin önerilerini çekerken hata oluştu: {e}", parent=ins_window)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
                
    tk.Button(filter_frame_ins, text="Filtrele/Yenile", command=load_filtered_insulin_recommendations).pack(side="left", padx=10)
    load_filtered_insulin_recommendations()


def confirm_and_mark_insulin_applied_by_patient(oneri_id, refresh_callback):
    if messagebox.askyesno("Onay", f"Bu insülin önerisini uyguladığınızdan emin misiniz?"):
        mark_insulin_applied_by_oneri_id(oneri_id)
        refresh_callback()

def mark_insulin_applied_by_oneri_id(oneri_id):
    conn = connect_db()
    if not conn: return
    cursor = conn.cursor()
    try:
        query = "UPDATE insulin_onerileri SET uygulandi = TRUE WHERE oneri_id = %s AND hasta_id = %s"
        cursor.execute(query, (oneri_id, current_patient_id)) 
        conn.commit()
        if cursor.rowcount > 0:
            messagebox.showinfo("Başarılı", "İnsülin önerisi uygulandı olarak işaretlendi!")
        else:
            messagebox.showwarning("Uyarı", "Öneri güncellenemedi veya zaten işaretlenmiş.")
    except Exception as e:
        messagebox.showerror("Hata", f"İnsülin önerisi güncellenirken hata oluştu: {e}")
        conn.rollback()
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def show_patient_notifications(parent_window, user_kullanici_id_param):
    notif_window = tk.Toplevel(parent_window)
    notif_window.title("Bildirimlerim")
    notif_window.geometry("700x550")

    tk.Label(notif_window, text="Size Gelen Son Bildirimler:", font=("Arial", 14, "bold")).pack(pady=10)
    
    controls_frame = tk.Frame(notif_window)
    controls_frame.pack(fill="x", padx=10)
    tk.Button(controls_frame, text="Listeyi Yenile", command=lambda: load_notifications_for_patient(scrollable_frame_notif, canvas_notif, scrollbar_notif, user_kullanici_id_param)).pack(side="right", pady=5)


    results_frame = tk.Frame(notif_window)
    results_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    canvas_notif = tk.Canvas(results_frame)
    scrollbar_notif = tk.Scrollbar(results_frame, orient="vertical", command=canvas_notif.yview)
    scrollable_frame_notif = tk.Frame(canvas_notif)
    scrollable_frame_notif.bind("<Configure>", lambda e: canvas_notif.configure(scrollregion=canvas_notif.bbox("all")))
    canvas_notif.create_window((0,0), window=scrollable_frame_notif, anchor="nw")
    canvas_notif.configure(yscrollcommand=scrollbar_notif.set)

    load_notifications_for_patient(scrollable_frame_notif, canvas_notif, scrollbar_notif, user_kullanici_id_param)


def load_notifications_for_patient(target_frame, target_canvas, target_scrollbar, user_id_for_notifs):
    for widget in target_frame.winfo_children():
        widget.destroy()

    conn = connect_db()
    if not conn: 
        tk.Label(target_frame, text="Veritabanı bağlantı hatası.").pack(pady=20)
        return
        
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT bildirim_id, baslik, mesaj, bildirim_tipi, okundu, olusturma_tarihi
            FROM bildirimler
            WHERE kullanici_id = %s
            ORDER BY olusturma_tarihi DESC
            LIMIT 50 
        """
        cursor.execute(query, (user_id_for_notifs,)) 
        notifications = cursor.fetchall()

        if notifications:
            for notif in notifications:
                bg_color = "lightyellow" if not notif['okundu'] and notif['bildirim_tipi'] == 'Uyarı' else \
                           "mistyrose" if not notif['okundu'] and notif['bildirim_tipi'] == 'Hata' else \
                           "lightcyan" if not notif['okundu'] else "lightgray"
                
                notif_item_frame = tk.LabelFrame(target_frame, 
                                                 text=f"{notif['baslik']} ({notif['bildirim_tipi']}) - {notif['olusturma_tarihi'].strftime('%d.%m.%Y %H:%M')}",
                                                 font=("Arial", 10, "bold"), bg=bg_color, padx=5, pady=5)
                notif_item_frame.pack(fill="x", padx=5, pady=3)

                tk.Label(notif_item_frame, text=notif['mesaj'], justify=tk.LEFT, font=("Arial", 9), bg=bg_color, anchor="w", wraplength=600).pack(anchor="w", fill="x")

                if not notif['okundu']:
                    def mark_notif_read_action(notif_id_to_mark=notif['bildirim_id'], frame=target_frame, canv=target_canvas, scrollb=target_scrollbar, user_id=user_id_for_notifs):
                        if update_notification_status_patient(notif_id_to_mark, True, user_id):
                            load_notifications_for_patient(frame, canv, scrollb, user_id)


                    tk.Button(notif_item_frame, text="Okundu İşaretle",
                              command=mark_notif_read_action, bg="skyblue", font=("Arial", 8)).pack(anchor="e", pady=2)
        else:
            tk.Label(target_frame, text="Henüz size gönderilmiş bir bildirim yok.", font=("Arial", 11)).pack(pady=30)
        
        target_canvas.pack(side="left", fill="both", expand=True)
        target_scrollbar.pack(side="right", fill="y")

    except Exception as e:
        messagebox.showerror("Hata", f"Bildirimler yüklenirken hata: {e}", parent=target_frame.winfo_toplevel())
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def update_notification_status_patient(bildirim_id, status_bool, user_id_for_update):
    conn_update = connect_db()
    if not conn_update: return False
    cursor_update = conn_update.cursor()
    updated = False
    try:
        query = "UPDATE bildirimler SET okundu = %s, okunma_tarihi = NOW() WHERE bildirim_id = %s AND kullanici_id = %s"
        cursor_update.execute(query, (status_bool, bildirim_id, user_id_for_update))
        conn_update.commit()
        if cursor_update.rowcount > 0:
            updated = True
    except Exception as e:
        messagebox.showerror("Hata", f"Bildirim durumu güncellenirken hata oluştu: {e}")
        conn_update.rollback()
    finally:
        if conn_update.is_connected():
            cursor_update.close()
            conn_update.close()
    return updated

def get_diyet_turleri():
    conn = connect_db()
    if not conn: return []
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT diyet_turu_id, diyet_adi FROM diyet_turleri ORDER BY diyet_adi")
        return cursor.fetchall() 
    except Exception as e:
        messagebox.showerror("Hata", f"Diyet türleri çekilirken hata oluştu: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_egzersiz_turleri():
    conn = connect_db()
    if not conn: return []
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT egzersiz_turu_id, egzersiz_adi FROM egzersiz_turleri ORDER BY egzersiz_adi")
        return cursor.fetchall() 
    except Exception as e:
        messagebox.showerror("Hata", f"Egzersiz türleri çekilirken hata oluştu: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def create_database_and_tables():
    conn = None
    cursor = None
    try:
        temp_config = DB_CONFIG.copy()
        temp_config.pop('database', None) 

        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS diyabet_takip_sistemi CHARACTER SET utf8mb4 COLLATE utf8mb4_turkish_ci")
        print("Veritabanı kontrol edildi/oluşturuldu.")

        conn.database = DB_CONFIG['database']

        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS kullanici_rolleri (
                rol_id INT PRIMARY KEY AUTO_INCREMENT,
                rol_adi VARCHAR(50) NOT NULL UNIQUE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS kullanicilar (
                kullanici_id INT PRIMARY KEY AUTO_INCREMENT,
                tc_kimlik_no CHAR(11) NOT NULL UNIQUE,
                sifre VARCHAR(255) NOT NULL,
                ad VARCHAR(100) NOT NULL,
                soyad VARCHAR(100) NOT NULL,
                dogum_tarihi DATE NOT NULL,
                cinsiyet ENUM('Erkek', 'Kadın') NOT NULL,
                eposta VARCHAR(255) NOT NULL UNIQUE,
                profil_resmi LONGBLOB,
                rol_id INT NOT NULL,
                aktif_durum BOOLEAN DEFAULT TRUE,
                kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                son_giris_tarihi TIMESTAMP NULL,
                FOREIGN KEY (rol_id) REFERENCES kullanici_rolleri(rol_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS doktorlar (
                doktor_id INT PRIMARY KEY AUTO_INCREMENT,
                kullanici_id INT NOT NULL UNIQUE,
                uzmanlik_alani VARCHAR(100),
                diploma_no VARCHAR(50),
                calisma_saatleri JSON,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS hastalar (
                hasta_id INT PRIMARY KEY AUTO_INCREMENT,
                kullanici_id INT NOT NULL UNIQUE,
                doktor_id INT NOT NULL,
                tani_tarihi DATE,
                diyabet_tipi ENUM('Tip 1', 'Tip 2', 'Gestasyonel') DEFAULT 'Tip 2',
                hedef_kan_sekeri_min INT DEFAULT 70,
                hedef_kan_sekeri_max INT DEFAULT 110,
                notlar TEXT,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE CASCADE,
                FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS diyet_turleri (
                diyet_turu_id INT PRIMARY KEY AUTO_INCREMENT,
                diyet_adi VARCHAR(100) NOT NULL UNIQUE,
                aciklama TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS egzersiz_turleri (
                egzersiz_turu_id INT PRIMARY KEY AUTO_INCREMENT,
                egzersiz_adi VARCHAR(100) NOT NULL UNIQUE,
                aciklama TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS belirtiler (
                belirti_id INT PRIMARY KEY AUTO_INCREMENT,
                belirti_adi VARCHAR(100) NOT NULL UNIQUE,
                aciklama TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS kan_sekeri_olcumleri (
                olcum_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                olcum_tarihi DATE NOT NULL,
                olcum_saati TIME NOT NULL,
                olcum_zamani DATETIME NOT NULL,
                kan_sekeri_degeri DECIMAL(5,2) NOT NULL,
                olcum_tipi ENUM('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece', 'Diğer') NOT NULL,
                gecerli_olcum BOOLEAN DEFAULT TRUE,
                notlar TEXT,
                kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                CONSTRAINT chk_kan_sekeri CHECK (kan_sekeri_degeri >= 0 AND kan_sekeri_degeri <= 1000)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS hasta_belirtileri (
                kayit_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                belirti_id INT NOT NULL,
                kayit_tarihi DATE NOT NULL,
                siddet_seviyesi ENUM('Hafif', 'Orta', 'Şiddetli') DEFAULT 'Orta',
                notlar TEXT,
                kayit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                FOREIGN KEY (belirti_id) REFERENCES belirtiler(belirti_id),
                UNIQUE KEY unique_hasta_belirti_tarih (hasta_id, belirti_id, kayit_tarihi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS diyet_planlari (
                plan_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                doktor_id INT NOT NULL,
                diyet_turu_id INT NOT NULL,
                baslangic_tarihi DATE NOT NULL,
                bitis_tarihi DATE,
                aktif_durum BOOLEAN DEFAULT TRUE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
                FOREIGN KEY (diyet_turu_id) REFERENCES diyet_turleri(diyet_turu_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS egzersiz_planlari (
                plan_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                doktor_id INT NOT NULL,
                egzersiz_turu_id INT NOT NULL,
                baslangic_tarihi DATE NOT NULL,
                bitis_tarihi DATE,
                haftalik_siklik INT DEFAULT 3,
                sure_dakika INT DEFAULT 30,
                aktif_durum BOOLEAN DEFAULT TRUE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
                FOREIGN KEY (egzersiz_turu_id) REFERENCES egzersiz_turleri(egzersiz_turu_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS diyet_takibi (
                takip_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                takip_tarihi DATE NOT NULL,
                diyet_uygulandimi BOOLEAN NOT NULL,
                notlar TEXT,
                kayit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                UNIQUE KEY unique_hasta_tarih (hasta_id, takip_tarihi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS egzersiz_takibi (
                takip_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                takip_tarihi DATE NOT NULL,
                egzersiz_yapildimi BOOLEAN NOT NULL,
                sure_dakika INT,
                notlar TEXT,
                kayit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                UNIQUE KEY unique_hasta_tarih_egz (hasta_id, takip_tarihi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS insulin_onerileri (
                oneri_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                tarih DATE NOT NULL,
                olcum_tipi ENUM('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece') NOT NULL,
                ortalama_kan_sekeri DECIMAL(5,2) NOT NULL,
                onerilen_doz_ml DECIMAL(3,1) NOT NULL,
                uygulandi BOOLEAN DEFAULT FALSE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                UNIQUE KEY unique_hasta_tarih_tip (hasta_id, tarih, olcum_tipi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS uyari_turleri (
                uyari_turu_id INT PRIMARY KEY AUTO_INCREMENT,
                uyari_adi VARCHAR(100) NOT NULL UNIQUE,
                aciklama TEXT,
                aciliyet_seviyesi ENUM('Düşük', 'Orta', 'Yüksek', 'Kritik') NOT NULL DEFAULT 'Orta'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS uyarilar (
                uyari_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                doktor_id INT NOT NULL,
                uyari_turu_id INT NOT NULL,
                uyari_mesaji TEXT NOT NULL,
                kan_sekeri_degeri DECIMAL(5,2),
                uyari_tarihi DATE NOT NULL,
                okundu BOOLEAN DEFAULT FALSE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
                FOREIGN KEY (uyari_turu_id) REFERENCES uyari_turleri(uyari_turu_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS sistem_loglari (
                log_id INT PRIMARY KEY AUTO_INCREMENT,
                kullanici_id INT,
                islem_tipi VARCHAR(100) NOT NULL,
                islem_detayi TEXT,
                ip_adresi VARCHAR(45),
                tarayici_bilgisi TEXT,
                islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS kural_tabani (
                kural_id INT PRIMARY KEY AUTO_INCREMENT,
                kan_sekeri_min DECIMAL(5,2),
                kan_sekeri_max DECIMAL(5,2),
                belirtiler JSON,
                onerilen_diyet_id INT,
                onerilen_egzersiz_id INT,
                aktif_durum BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (onerilen_diyet_id) REFERENCES diyet_turleri(diyet_turu_id),
                FOREIGN KEY (onerilen_egzersiz_id) REFERENCES egzersiz_turleri(egzersiz_turu_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS hasta_uyum_skorlari (
                skor_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                hesaplama_tarihi DATE NOT NULL,
                diyet_uyum_orani DECIMAL(5,2) DEFAULT 0,
                egzersiz_uyum_orani DECIMAL(5,2) DEFAULT 0,
                olcum_uyum_orani DECIMAL(5,2) DEFAULT 0,
                genel_uyum_skoru DECIMAL(5,2) DEFAULT 0,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                UNIQUE KEY unique_hasta_tarih_skor (hasta_id, hesaplama_tarihi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS bildirimler (
                bildirim_id INT PRIMARY KEY AUTO_INCREMENT,
                kullanici_id INT NOT NULL,
                baslik VARCHAR(200) NOT NULL,
                mesaj TEXT NOT NULL,
                bildirim_tipi ENUM('Bilgi', 'Uyarı', 'Hata', 'Başarı') DEFAULT 'Bilgi',
                okundu BOOLEAN DEFAULT FALSE,
                okunma_tarihi TIMESTAMP NULL,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(kullanici_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS sistem_ayarlari (
                ayar_id INT PRIMARY KEY AUTO_INCREMENT,
                ayar_anahtari VARCHAR(100) NOT NULL UNIQUE,
                ayar_degeri TEXT NOT NULL,
                aciklama TEXT,
                veri_tipi ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS hasta_hedefleri (
                hedef_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                hedef_tipi ENUM('Kan Şekeri', 'Kilo', 'Egzersiz', 'Diyet') NOT NULL,
                hedef_degeri DECIMAL(8,2) NOT NULL,
                olcum_birimi VARCHAR(20) NOT NULL,
                baslangic_tarihi DATE NOT NULL,
                bitis_tarihi DATE,
                mevcut_durum DECIMAL(8,2),
                aktif_durum BOOLEAN DEFAULT TRUE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS doktor_hasta_notlari (
                not_id INT PRIMARY KEY AUTO_INCREMENT,
                doktor_id INT NOT NULL,
                hasta_id INT NOT NULL,
                not_basligi VARCHAR(200) NOT NULL,
                not_icerigi TEXT NOT NULL,
                etiketler JSON,
                onem_seviyesi ENUM('Düşük', 'Orta', 'Yüksek') DEFAULT 'Orta',
                gorunurluk ENUM('Sadece Doktor', 'Doktor ve Hasta') DEFAULT 'Sadece Doktor',
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS kan_sekeri_istatistikleri (
                istatistik_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                istatistik_tarihi DATE NOT NULL,
                minimum_deger DECIMAL(5,2),
                maksimum_deger DECIMAL(5,2),
                ortalama_deger DECIMAL(5,2),
                standart_sapma DECIMAL(5,2),
                olcum_sayisi INT DEFAULT 0,
                hedef_aralik_uyum_yuzdesi DECIMAL(5,2),
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE,
                UNIQUE KEY unique_hasta_tarih_istatistik (hasta_id, istatistik_tarihi)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS randevu_sistemi (
                randevu_id INT PRIMARY KEY AUTO_INCREMENT,
                doktor_id INT NOT NULL,
                hasta_id INT NOT NULL,
                randevu_tarihi DATE NOT NULL,
                randevu_saati TIME NOT NULL,
                randevu_suresi INT DEFAULT 30,
                randevu_durumu ENUM('Planlandı', 'Onaylandı', 'Tamamlandı', 'İptal Edildi') DEFAULT 'Planlandı',
                randevu_notu TEXT,
                hatirlatma_gonderildi BOOLEAN DEFAULT FALSE,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doktor_id) REFERENCES doktorlar(doktor_id),
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS ilac_takibi (
                takip_id INT PRIMARY KEY AUTO_INCREMENT,
                hasta_id INT NOT NULL,
                ilac_adi VARCHAR(200) NOT NULL,
                doz VARCHAR(100) NOT NULL,
                kullanim_saatleri JSON NOT NULL,
                baslangic_tarihi DATE NOT NULL,
                bitis_tarihi DATE,
                yan_etkiler TEXT,
                aktif_durum BOOLEAN DEFAULT TRUE,
                doktor_notu TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hasta_id) REFERENCES hastalar(hasta_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            CREATE TABLE IF NOT EXISTS ilac_kullanim_kayitlari (
                kayit_id INT PRIMARY KEY AUTO_INCREMENT,
                takip_id INT NOT NULL,
                kullanim_tarihi DATE NOT NULL,
                kullanim_saati TIME NOT NULL,
                kullanildi BOOLEAN NOT NULL,
                gecikme_suresi INT DEFAULT 0,
                not_metni TEXT,
                kayit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (takip_id) REFERENCES ilac_takibi(takip_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_turkish_ci;
            """,
            """
            DROP TRIGGER IF EXISTS kan_sekeri_uyari_kontrol;
            """,
            """
            CREATE TRIGGER kan_sekeri_uyari_kontrol
            AFTER INSERT ON kan_sekeri_olcumleri
            FOR EACH ROW
            BEGIN
                DECLARE doktor_id_var INT;
                DECLARE uyari_mesaji_var TEXT;
                DECLARE uyari_turu_id_var INT;
                DECLARE hipoglisemi_esik DECIMAL(5,2);
                DECLARE hiperglisemi_esik DECIMAL(5,2);

                SELECT CAST(ayar_degeri AS DECIMAL(5,2)) INTO hipoglisemi_esik FROM sistem_ayarlari WHERE ayar_anahtari = 'hipoglisemi_esik';
                SELECT CAST(ayar_degeri AS DECIMAL(5,2)) INTO hiperglisemi_esik FROM sistem_ayarlari WHERE ayar_anahtari = 'hiperglisemi_esik';

                SELECT h.doktor_id INTO doktor_id_var
                FROM hastalar h
                WHERE h.hasta_id = NEW.hasta_id;

                IF NEW.gecerli_olcum = TRUE THEN
                    IF NEW.kan_sekeri_degeri < hipoglisemi_esik THEN
                        SET uyari_mesaji_var = CONCAT('Hastanın kan şekeri seviyesi ', NEW.kan_sekeri_degeri, ' mg/dL''nin altına düştü. Hipoglisemi riski! Hızlı müdahale gerekebilir.');
                        SET uyari_turu_id_var = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Acil Uyarı');
                    ELSEIF NEW.kan_sekeri_degeri > hiperglisemi_esik THEN
                        SET uyari_mesaji_var = CONCAT('Hastanın kan şekeri ', NEW.kan_sekeri_degeri, ' mg/dL''nin üzerinde. Hiperglisemi durumu. Acil müdahale gerekebilir.');
                        SET uyari_turu_id_var = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Acil Müdahale Uyarısı');
                    ELSEIF NEW.kan_sekeri_degeri BETWEEN 151 AND 200 THEN
                        SET uyari_mesaji_var = CONCAT('Hastanın kan şekeri ', NEW.kan_sekeri_degeri, ' mg/dL arasında. Diyabet kontrolü gereklidir.');
                        SET uyari_turu_id_var = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'İzleme Uyarısı');
                    ELSEIF NEW.kan_sekeri_degeri BETWEEN 111 AND 150 THEN
                        SET uyari_mesaji_var = CONCAT('Hastanın kan şekeri ', NEW.kan_sekeri_degeri, ' mg/dL arasında. Durum izlenmeli.');
                        SET uyari_turu_id_var = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Takip Uyarısı');
                    END IF;
                    IF uyari_mesaji_var IS NOT NULL THEN
                        INSERT INTO uyarilar (hasta_id, doktor_id, uyari_turu_id, uyari_tarihi, uyari_mesaji, kan_sekeri_degeri)
                        VALUES (NEW.hasta_id, doktor_id_var, uyari_turu_id_var, NEW.olcum_tarihi, uyari_mesaji_var, NEW.kan_sekeri_degeri);
                    END IF;
                ELSE
                    INSERT INTO bildirimler (kullanici_id, baslik, mesaj, bildirim_tipi)
                    SELECT h.kullanici_id, 'Ölçüm Zamanı Uyarısı',
                               CONCAT('Girdiğiniz kan şekeri ölçümü (', NEW.kan_sekeri_degeri, ' mg/dL) belirtilen saat aralığının dışındadır (', DATE_FORMAT(NEW.olcum_zamani, '%d.%m.%Y %H:%i:%s'), '). Bu ölçüm ortalamaya dahil edilmeyecektir. Lütfen istenilen saat aralığında ölçüm yapınız.'),
                               'Uyarı'
                    FROM hastalar h
                    WHERE h.hasta_id = NEW.hasta_id;
                END IF;
            END;
            """,
            """
            DROP FUNCTION IF EXISTS gunluk_ortalama_hesapla;
            """,
            """
            CREATE FUNCTION gunluk_ortalama_hesapla(hasta_id_param INT, tarih_param DATE)
            RETURNS DECIMAL(5,2)
            READS SQL DATA
            DETERMINISTIC
            BEGIN
                DECLARE ortalama DECIMAL(5,2) DEFAULT 0;
                SELECT AVG(kan_sekeri_degeri) INTO ortalama
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = hasta_id_param
                AND DATE(olcum_zamani) = tarih_param
                AND gecerli_olcum = TRUE;
                RETURN IFNULL(ortalama, 0);
            END;
            """,
            """
            DROP FUNCTION IF EXISTS ogun_ortalama_kan_sekeri_hesapla;
            """,
            """
            CREATE FUNCTION ogun_ortalama_kan_sekeri_hesapla(
                hasta_id_param INT,
                tarih_param DATE,
                olcum_tipi_param ENUM('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece')
            )
            RETURNS DECIMAL(5,2)
            READS SQL DATA
            DETERMINISTIC
            BEGIN
                DECLARE ortalama_deger DECIMAL(5,2);
                DECLARE total_sum DECIMAL(10,2) DEFAULT 0;
                DECLARE num_measurements INT DEFAULT 0;
                IF olcum_tipi_param = 'Sabah' THEN
                    SELECT SUM(kan_sekeri_degeri), COUNT(*)
                    INTO total_sum, num_measurements
                    FROM kan_sekeri_olcumleri
                    WHERE hasta_id = hasta_id_param
                    AND DATE(olcum_zamani) = tarih_param
                    AND olcum_tipi = 'Sabah'
                    AND gecerli_olcum = TRUE;
                ELSEIF olcum_tipi_param = 'Öğle' THEN
                    SELECT SUM(kan_sekeri_degeri), COUNT(*)
                    INTO total_sum, num_measurements
                    FROM kan_sekeri_olcumleri
                    WHERE hasta_id = hasta_id_param
                    AND DATE(olcum_zamani) = tarih_param
                    AND olcum_tipi IN ('Sabah', 'Öğle')
                    AND gecerli_olcum = TRUE;
                ELSEIF olcum_tipi_param = 'İkindi' THEN
                    SELECT SUM(kan_sekeri_degeri), COUNT(*)
                    INTO total_sum, num_measurements
                    FROM kan_sekeri_olcumleri
                    WHERE hasta_id = hasta_id_param
                    AND DATE(olcum_zamani) = tarih_param
                    AND olcum_tipi IN ('Sabah', 'Öğle', 'İkindi')
                    AND gecerli_olcum = TRUE;
                ELSEIF olcum_tipi_param = 'Akşam' THEN
                    SELECT SUM(kan_sekeri_degeri), COUNT(*)
                    INTO total_sum, num_measurements
                    FROM kan_sekeri_olcumleri
                    WHERE hasta_id = hasta_id_param
                    AND DATE(olcum_zamani) = tarih_param
                    AND olcum_tipi IN ('Sabah', 'Öğle', 'İkindi', 'Akşam')
                    AND gecerli_olcum = TRUE;
                ELSEIF olcum_tipi_param = 'Gece' THEN
                    SELECT SUM(kan_sekeri_degeri), COUNT(*)
                    INTO total_sum, num_measurements
                    FROM kan_sekeri_olcumleri
                    WHERE hasta_id = hasta_id_param
                    AND DATE(olcum_zamani) = tarih_param
                    AND olcum_tipi IN ('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece')
                    AND gecerli_olcum = TRUE;
                END IF;
                IF num_measurements > 0 THEN
                    SET ortalama_deger = total_sum / num_measurements;
                ELSE
                    SET ortalama_deger = 0;
                END IF;
                RETURN ortalama_deger;
            END;
            """,
            """
            DROP FUNCTION IF EXISTS insulin_doz_hesapla;
            """,
            """
            CREATE FUNCTION insulin_doz_hesapla(ortalama_kan_sekeri DECIMAL(5,2))
            RETURNS DECIMAL(3,1)
            READS SQL DATA
            DETERMINISTIC
            BEGIN
                DECLARE doz DECIMAL(3,1) DEFAULT 0;
                IF ortalama_kan_sekeri < 70 THEN
                    SET doz = 0;
                ELSEIF ortalama_kan_sekeri BETWEEN 70 AND 110 THEN
                    SET doz = 0;
                ELSEIF ortalama_kan_sekeri BETWEEN 111 AND 150 THEN
                    SET doz = 1.0;
                ELSEIF ortalama_kan_sekeri BETWEEN 151 AND 200 THEN
                    SET doz = 2.0;
                ELSEIF ortalama_kan_sekeri > 200 THEN
                    SET doz = 3.0;
                END IF;
                RETURN doz;
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS insulin_onerisi_olustur;
            """,
            """
            CREATE PROCEDURE insulin_onerisi_olustur(
                IN hasta_id_param INT,
                IN tarih_param DATE,
                IN olcum_tipi_param ENUM('Sabah', 'Öğle', 'İkindi', 'Akşam', 'Gece')
            )
            BEGIN
                DECLARE avg_blood_sugar DECIMAL(5,2);
                DECLARE recommended_dose DECIMAL(3,1);
                SET avg_blood_sugar = ogun_ortalama_kan_sekeri_hesapla(hasta_id_param, tarih_param, olcum_tipi_param);
                IF avg_blood_sugar > 0 THEN
                    SET recommended_dose = insulin_doz_hesapla(avg_blood_sugar);
                    INSERT INTO insulin_onerileri (hasta_id, tarih, olcum_tipi, ortalama_kan_sekeri, onerilen_doz_ml)
                    VALUES (hasta_id_param, tarih_param, olcum_tipi_param, avg_blood_sugar, recommended_dose)
                    ON DUPLICATE KEY UPDATE
                        ortalama_kan_sekeri = VALUES(ortalama_kan_sekeri),
                        onerilen_doz_ml = VALUES(onerilen_doz_ml);
                END IF;
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS gunluk_insulin_onerileri_yonet;
            """,
            """
            CREATE PROCEDURE gunluk_insulin_onerileri_yonet(IN hasta_id_param INT, IN tarih_param DATE)
            BEGIN
                CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'Sabah');
                CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'Öğle');
                CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'İkindi');
                CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'Akşam');
                CALL insulin_onerisi_olustur(hasta_id_param, tarih_param, 'Gece');
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS gunluk_olcum_kontrol_ve_uyari;
            """,
            """
            CREATE PROCEDURE gunluk_olcum_kontrol_ve_uyari()
            BEGIN
                DECLARE done INT DEFAULT FALSE;
                DECLARE hasta_id_var INT;
                DECLARE doktor_id_var INT;
                DECLARE olcum_sayisi_bugun INT;
                DECLARE gunluk_minimum_olcum INT;

                DECLARE hasta_cursor CURSOR FOR
                    SELECT h.hasta_id, h.doktor_id
                    FROM hastalar h
                    JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
                    WHERE k.aktif_durum = TRUE;

                DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

                SELECT CAST(ayar_degeri AS UNSIGNED) INTO gunluk_minimum_olcum
                FROM sistem_ayarlari
                WHERE ayar_anahtari = 'minimum_gunluk_olcum';

                OPEN hasta_cursor;

                hasta_loop: LOOP
                    FETCH hasta_cursor INTO hasta_id_var, doktor_id_var;

                    IF done THEN
                        LEAVE hasta_loop;
                    END IF;

                    SELECT COUNT(*) INTO olcum_sayisi_bugun
                    FROM kan_sekeri_olcumleri
                    WHERE hasta_id = hasta_id_var
                    AND DATE(olcum_zamani) = CURDATE() - INTERVAL 1 DAY
                    AND gecerli_olcum = TRUE;

                    IF olcum_sayisi_bugun = 0 THEN
                        INSERT INTO uyarilar (hasta_id, doktor_id, uyari_turu_id, uyari_tarihi, uyari_mesaji)
                        VALUES (hasta_id_var, doktor_id_var, (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Ölçüm Eksik Uyarısı'), CURDATE() - INTERVAL 1 DAY, 'Hasta bir önceki gün boyunca kan şekeri ölçümü yapmamıştır. Acil takip önerilir.');
                    ELSEIF olcum_sayisi_bugun < gunluk_minimum_olcum THEN
                        INSERT INTO uyarilar (hasta_id, doktor_id, uyari_turu_id, uyari_tarihi, uyari_mesaji)
                        VALUES (hasta_id_var, doktor_id_var, (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Ölçüm Yetersiz Uyarısı'), CURDATE() - INTERVAL 1 DAY, CONCAT('Hastanın bir önceki günkü kan şekeri ölçüm sayısı yetersiz (', olcum_sayisi_bugun, '/5). Durum izlenmelidir.'));
                    END IF;

                END LOOP;

                CLOSE hasta_cursor;
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS hasta_uyum_skoru_hesapla;
            """,
            """
            CREATE PROCEDURE hasta_uyum_skoru_hesapla(IN hasta_id_param INT, IN tarih_param DATE)
            BEGIN
                DECLARE diyet_uyum DECIMAL(5,2) DEFAULT 0;
                DECLARE egzersiz_uyum DECIMAL(5,2) DEFAULT 0;
                DECLARE olcum_uyum DECIMAL(5,2) DEFAULT 0;
                DECLARE genel_skor DECIMAL(5,2) DEFAULT 0;
                DECLARE son_7_gun_toplam_gun INT DEFAULT 7;

                SELECT
                    IFNULL((SUM(CASE WHEN diyet_uygulandimi = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 0)
                INTO diyet_uyum
                FROM diyet_takibi
                WHERE hasta_id = hasta_id_param
                AND takip_tarihi BETWEEN DATE_SUB(tarih_param, INTERVAL son_7_gun_toplam_gun - 1 DAY) AND tarih_param;

                SELECT
                    IFNULL((SUM(CASE WHEN egzersiz_yapildimi = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 0)
                INTO egzersiz_uyum
                FROM egzersiz_takibi
                WHERE hasta_id = hasta_id_param
                AND takip_tarihi BETWEEN DATE_SUB(tarih_param, INTERVAL son_7_gun_toplam_gun - 1 DAY) AND tarih_param;

                SELECT
                    IFNULL((COUNT(DISTINCT DATE(olcum_zamani)) * 100.0 / son_7_gun_toplam_gun), 0)
                INTO olcum_uyum
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = hasta_id_param
                AND DATE(olcum_zamani) BETWEEN DATE_SUB(tarih_param, INTERVAL son_7_gun_toplam_gun - 1 DAY) AND tarih_param
                AND gecerli_olcum = TRUE;

                SET genel_skor = (diyet_uyum * 0.4) + (egzersiz_uyum * 0.3) + (olcum_uyum * 0.3);

                INSERT INTO hasta_uyum_skorlari (hasta_id, hesaplama_tarihi, diyet_uyum_orani, egzersiz_uyum_orani, olcum_uyum_orani, genel_uyum_skoru)
                VALUES (hasta_id_param, tarih_param, diyet_uyum, egzersiz_uyum, olcum_uyum, genel_skor)
                ON DUPLICATE KEY UPDATE
                    diyet_uyum_orani = VALUES(diyet_uyum_orani),
                    egzersiz_uyum_orani = VALUES(egzersiz_uyum_orani),
                    olcum_uyum_orani = VALUES(olcum_uyum_orani),
                    genel_uyum_skoru = VALUES(genel_uyum_skoru);
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS gunluk_istatistik_hesapla;
            """,
            """
            CREATE PROCEDURE gunluk_istatistik_hesapla(IN hasta_id_param INT, IN tarih_param DATE)
            BEGIN
                DECLARE min_deger DECIMAL(5,2);
                DECLARE max_deger DECIMAL(5,2);
                DECLARE ort_deger DECIMAL(5,2);
                DECLARE std_sapma DECIMAL(5,2);
                DECLARE olcum_count INT;
                DECLARE hedef_uyum DECIMAL(5,2);
                DECLARE hedef_min DECIMAL(5,2);
                DECLARE hedef_max DECIMAL(5,2);

                SELECT hedef_kan_sekeri_min, hedef_kan_sekeri_max
                INTO hedef_min, hedef_max
                FROM hastalar
                WHERE hasta_id = hasta_id_param;

                SELECT
                    MIN(kan_sekeri_degeri),
                    MAX(kan_sekeri_degeri),
                    AVG(kan_sekeri_degeri),
                    STDDEV(kan_sekeri_degeri),
                    COUNT(*)
                INTO min_deger, max_deger, ort_deger, std_sapma, olcum_count
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = hasta_id_param
                AND DATE(olcum_zamani) = tarih_param
                AND gecerli_olcum = TRUE;

                SELECT
                    IFNULL((SUM(CASE WHEN kan_sekeri_degeri BETWEEN hedef_min AND hedef_max THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 0)
                INTO hedef_uyum
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = hasta_id_param
                AND DATE(olcum_zamani) = tarih_param
                AND gecerli_olcum = TRUE;

                INSERT INTO kan_sekeri_istatistikleri
                (hasta_id, istatistik_tarihi, minimum_deger, maksimum_deger, ortalama_deger, standart_sapma, olcum_sayisi, hedef_aralik_uyum_yuzdesi)
                VALUES (hasta_id_param, tarih_param, min_deger, max_deger, ort_deger, std_sapma, olcum_count, hedef_uyum)
                ON DUPLICATE KEY UPDATE
                    minimum_deger = VALUES(minimum_deger),
                    maksimum_deger = VALUES(maksimum_deger),
                    ortalama_deger = VALUES(ortalama_deger),
                    standart_sapma = VALUES(standart_sapma),
                    olcum_sayisi = VALUES(olcum_sayisi),
                    hedef_aralik_uyum_yuzdesi = VALUES(hedef_aralik_uyum_yuzdesi);
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS kural_tabanli_oneri_getir;
            """,
            """
            CREATE PROCEDURE kural_tabanli_oneri_getir(IN kan_sekeri_param DECIMAL(5,2), IN belirtiler_json_param JSON)
            BEGIN
                SELECT
                    kt.kural_id,
                    dt.diyet_adi AS onerilen_diyet,
                    et.egzersiz_adi AS onerilen_egzersiz,
                    kt.kan_sekeri_min,
                    kt.kan_sekeri_max,
                    kt.belirtiler
                FROM kural_tabani kt
                LEFT JOIN diyet_turleri dt ON kt.onerilen_diyet_id = dt.diyet_turu_id
                LEFT JOIN egzersiz_turleri et ON kt.onerilen_egzersiz_id = et.egzersiz_turu_id
                WHERE kt.aktif_durum = TRUE
                AND kan_sekeri_param BETWEEN kt.kan_sekeri_min AND kt.kan_sekeri_max
                AND JSON_OVERLAPS(kt.belirtiler, belirtiler_json_param)
                ORDER BY
                    ABS(kan_sekeri_param - ((kt.kan_sekeri_min + kt.kan_sekeri_max) / 2))
                LIMIT 1;
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS hasta_rapor_olustur;
            """,
            """
            CREATE PROCEDURE hasta_rapor_olustur(IN hasta_id_param INT, IN baslangic_tarihi DATE, IN bitis_tarihi DATE)
            BEGIN
                SELECT
                    'Genel Bilgiler' AS bolum,
                    JSON_OBJECT(
                        'hasta_adi', CONCAT(k.ad, ' ', k.soyad),
                        'tc_kimlik', k.tc_kimlik_no,
                        'diyabet_tipi', h.diyabet_tipi,
                        'tani_tarihi', h.tani_tarihi,
                        'doktor_adi', CONCAT(dk.ad, ' ', dk.soyad),
                        'rapor_araligi', JSON_OBJECT('baslangic', baslangic_tarihi, 'bitis', bitis_tarihi)
                    ) AS veri
                FROM hastalar h
                JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
                JOIN doktorlar d ON h.doktor_id = d.doktor_id
                JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
                WHERE h.hasta_id = hasta_id_param
                UNION ALL
                SELECT
                    'Kan Şekeri İstatistikleri' AS bolum,
                    JSON_OBJECT(
                        'ortalama', ROUND(AVG(kan_sekeri_degeri), 2),
                        'minimum', MIN(kan_sekeri_degeri),
                        'maksimum', MAX(kan_sekeri_degeri),
                        'olcum_sayisi', COUNT(*),
                        'normal_aralik_uyum', ROUND(
                            SUM(CASE WHEN kan_sekeri_degeri BETWEEN 70 AND 110 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
                        )
                    ) AS veri
                FROM kan_sekeri_olcumleri
                WHERE hasta_id = hasta_id_param
                AND DATE(olcum_zamani) BETWEEN baslangic_tarihi AND bitis_tarihi
                AND gecerli_olcum = TRUE
                HAVING COUNT(*) > 0
                UNION ALL
                SELECT
                    'Uyum Skorları' AS bolum,
                    JSON_OBJECT(
                        'ortalama_diyet_uyum', ROUND(AVG(diyet_uyum_orani), 2),
                        'ortalama_egzersiz_uyum', ROUND(AVG(egzersiz_uyum_orani), 2),
                        'ortalama_olcum_uyum', ROUND(AVG(olcum_uyum_orani), 2),
                        'genel_uyum_skoru', ROUND(AVG(genel_uyum_skoru), 2)
                    ) AS veri
                FROM hasta_uyum_skorlari
                WHERE hasta_id = hasta_id_param
                AND hesaplama_tarihi BETWEEN baslangic_tarihi AND bitis_tarihi
                HAVING COUNT(*) > 0
                UNION ALL
                SELECT
                    'Uyarı İstatistikleri' AS bolum,
                    JSON_OBJECT(
                        'toplam_uyari', COUNT(*),
                        'acil_uyari', SUM(CASE WHEN uyari_turu_id = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Acil Uyarı') THEN 1 ELSE 0 END),
                        'hiperglisemi_uyari', SUM(CASE WHEN uyari_turu_id = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Acil Müdahale Uyarısı') THEN 1 ELSE 0 END),
                        'olcum_eksik_uyari', SUM(CASE WHEN uyari_turu_id = (SELECT uyari_turu_id FROM uyari_turleri WHERE uyari_adi = 'Ölçüm Eksik Uyarısı') THEN 1 ELSE 0 END)
                    ) AS veri
                FROM uyarilar
                WHERE hasta_id = hasta_id_param
                AND uyari_tarihi BETWEEN baslangic_tarihi AND bitis_tarihi
                HAVING COUNT(*) > 0;
            END;
            """,
            """
            DROP VIEW IF EXISTS hasta_ozet_bilgileri;
            """,
            """
            CREATE VIEW hasta_ozet_bilgileri AS
            SELECT
                h.hasta_id,
                CONCAT(k.ad, ' ', k.soyad) AS hasta_adi,
                k.tc_kimlik_no,
                k.dogum_tarihi,
                k.cinsiyet,
                k.eposta,
                h.diyabet_tipi,
                h.tani_tarihi,
                CONCAT(dk.ad, ' ', dk.soyad) AS doktor_adi,
                (SELECT COUNT(*) FROM kan_sekeri_olcumleri ks WHERE ks.hasta_id = h.hasta_id AND DATE(ks.olcum_zamani) = CURDATE() AND ks.gecerli_olcum = TRUE) AS bugun_gecerli_olcum_sayisi,
                (SELECT AVG(ks.kan_sekeri_degeri) FROM kan_sekeri_olcumleri ks WHERE ks.hasta_id = h.hasta_id AND DATE(ks.olcum_zamani) = CURDATE() AND ks.gecerli_olcum = TRUE) AS bugun_ortalama_kan_sekeri
            FROM hastalar h
            JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
            JOIN doktorlar d ON h.doktor_id = d.doktor_id
            JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
            WHERE k.aktif_durum = TRUE;
            """,
            """
            DROP VIEW IF EXISTS doktor_hasta_listesi;
            """,
            """
            CREATE VIEW doktor_hasta_listesi AS
            SELECT
                d.doktor_id,
                CONCAT(dk.ad, ' ', dk.soyad) AS doktor_adi,
                h.hasta_id,
                CONCAT(hk.ad, ' ', hk.soyad) AS hasta_adi,
                hk.tc_kimlik_no,
                h.diyabet_tipi,
                h.tani_tarihi,
                (SELECT COUNT(*) FROM uyarilar u WHERE u.hasta_id = h.hasta_id AND u.okundu = FALSE) AS okunmamis_uyari_sayisi
            FROM doktorlar d
            JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
            JOIN hastalar h ON d.doktor_id = h.doktor_id
            JOIN kullanicilar hk ON h.kullanici_id = hk.kullanici_id
            WHERE dk.aktif_durum = TRUE AND hk.aktif_durum = TRUE;
            """,
            """
            DROP VIEW IF EXISTS haftalik_performans;
            """,
            """
            CREATE VIEW haftalik_performans AS
            SELECT
                h.hasta_id,
                YEARWEEK(COALESCE(dt.takip_tarihi, et.takip_tarihi)) AS hafta,
                COUNT(DISTINCT COALESCE(dt.takip_tarihi, et.takip_tarihi)) AS toplam_kayit_gunu,
                SUM(CASE WHEN dt.diyet_uygulandimi = TRUE THEN 1 ELSE 0 END) AS diyet_uygulanan_gun,
                SUM(CASE WHEN et.egzersiz_yapildimi = TRUE THEN 1 ELSE 0 END) AS egzersiz_yapilan_gun,
                ROUND(IFNULL((SUM(CASE WHEN dt.diyet_uygulandimi = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(dt.takip_id)), 0), 2) AS diyet_uyum_yuzdesi,
                ROUND(IFNULL((SUM(CASE WHEN et.egzersiz_yapildimi = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(et.takip_id)), 0), 2) AS egzersiz_uyum_yuzdesi
            FROM hastalar h
            LEFT JOIN diyet_takibi dt ON h.hasta_id = dt.hasta_id AND dt.takip_tarihi >= DATE_SUB(CURDATE(), INTERVAL 4 WEEK)
            LEFT JOIN egzersiz_takibi et ON h.hasta_id = et.hasta_id AND et.takip_tarihi >= DATE_SUB(CURDATE(), INTERVAL 4 WEEK) AND dt.takip_tarihi = et.takip_tarihi
            WHERE dt.takip_id IS NOT NULL OR et.takip_id IS NOT NULL
            GROUP BY h.hasta_id, YEARWEEK(COALESCE(dt.takip_tarihi, et.takip_tarihi));
            """,
            """
            DROP VIEW IF EXISTS hasta_performans_detay;
            """,
            """
            CREATE VIEW hasta_performans_detay AS
            SELECT
                h.hasta_id,
                CONCAT(k.ad, ' ', k.soyad) AS hasta_adi,
                DATE(ks.olcum_zamani) AS tarih,
                ks.olcum_tipi,
                ks.kan_sekeri_degeri,
                dt.diyet_uygulandimi,
                (SELECT diyet_adi FROM diyet_planlari dpl JOIN diyet_turleri dt_t ON dpl.diyet_turu_id = dt_t.diyet_turu_id WHERE dpl.hasta_id = h.hasta_id AND DATE(ks.olcum_zamani) BETWEEN dpl.baslangic_tarihi AND IFNULL(dpl.bitis_tarihi, '9999-12-31') AND dpl.aktif_durum = TRUE LIMIT 1) AS uygulanan_diyet_adi,
                et.egzersiz_yapildimi,
                (SELECT egzersiz_adi FROM egzersiz_planlari epl JOIN egzersiz_turleri et_t ON epl.egzersiz_turu_id = et_t.egzersiz_turu_id WHERE epl.hasta_id = h.hasta_id AND DATE(ks.olcum_zamani) BETWEEN epl.baslangic_tarihi AND IFNULL(epl.bitis_tarihi, '9999-12-31') AND epl.aktif_durum = TRUE LIMIT 1) AS uygulanan_egzersiz_adi,
                CASE
                    WHEN ks.kan_sekeri_degeri BETWEEN h.hedef_kan_sekeri_min AND h.hedef_kan_sekeri_max THEN 'Hedefte'
                    WHEN ks.kan_sekeri_degeri < h.hedef_kan_sekeri_min THEN 'Düşük'
                    ELSE 'Yüksek'
                END AS kan_sekeri_durumu
            FROM hastalar h
            JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
            LEFT JOIN kan_sekeri_olcumleri ks ON h.hasta_id = ks.hasta_id AND ks.gecerli_olcum = TRUE
            LEFT JOIN diyet_takibi dt ON h.hasta_id = dt.hasta_id AND DATE(ks.olcum_zamani) = dt.takip_tarihi
            LEFT JOIN egzersiz_takibi et ON h.hasta_id = et.hasta_id AND DATE(ks.olcum_zamani) = et.takip_tarihi
            WHERE ks.olcum_id IS NOT NULL
            ORDER BY h.hasta_id, DATE(ks.olcum_zamani), ks.olcum_zamani;
            """,
            """
            DROP VIEW IF EXISTS doktor_dashboard;
            """,
            """
            CREATE VIEW doktor_dashboard AS
            SELECT
                d.doktor_id,
                CONCAT(dk.ad, ' ', dk.soyad) AS doktor_adi,
                COUNT(DISTINCT h.hasta_id) AS toplam_hasta_sayisi,
                COUNT(DISTINCT CASE WHEN DATE(ks.olcum_zamani) = CURDATE() THEN h.hasta_id END) AS bugun_olcum_yapan_hasta_sayisi,
                COUNT(DISTINCT CASE WHEN u.okundu = FALSE THEN u.uyari_id END) AS okunmamis_uyari_sayisi,
                COUNT(DISTINCT CASE WHEN u.uyari_tarihi = CURDATE() THEN u.uyari_id END) AS bugun_uyari_sayisi,
                ROUND(AVG(hus.genel_uyum_skoru), 2) AS ortalama_hasta_uyum_skoru
            FROM doktorlar d
            JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id
            LEFT JOIN hastalar h ON d.doktor_id = h.doktor_id
            LEFT JOIN kan_sekeri_olcumleri ks ON h.hasta_id = ks.hasta_id AND ks.gecerli_olcum = TRUE
            LEFT JOIN uyarilar u ON d.doktor_id = u.doktor_id
            LEFT JOIN hasta_uyum_skorlari hus ON h.hasta_id = hus.hasta_id AND hus.hesaplama_tarihi >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            WHERE dk.aktif_durum = TRUE
            GROUP BY d.doktor_id, doktor_adi;
            """,
            """
            DROP VIEW IF EXISTS kritik_hastalar;
            """,
            """
            CREATE VIEW kritik_hastalar AS
            SELECT
                h.hasta_id,
                CONCAT(k.ad, ' ', k.soyad) AS hasta_adi,
                h.doktor_id,
                IFNULL(AVG(ks.kan_sekeri_degeri), 0) AS son_7_gun_ortalama_kan_sekeri,
                COUNT(DISTINCT DATE(ks.olcum_zamani)) AS son_7_gun_olcum_gun_sayisi,
                SUM(CASE WHEN ut.aciliyet_seviyesi = 'Kritik' THEN 1 ELSE 0 END) AS kritik_uyari_sayisi,
                IFNULL(hus.genel_uyum_skoru, 0) AS son_uyum_skoru,
                CASE
                    WHEN IFNULL(AVG(ks.kan_sekeri_degeri), 0) < (SELECT CAST(ayar_degeri AS DECIMAL(5,2)) FROM sistem_ayarlari WHERE ayar_anahtari = 'hipoglisemi_esik')
                         OR IFNULL(AVG(ks.kan_sekeri_degeri), 0) > (SELECT CAST(ayar_degeri AS DECIMAL(5,2)) FROM sistem_ayarlari WHERE ayar_anahtari = 'hiperglisemi_esik') THEN 'Kritik Durum (Kan Şekeri)'
                    WHEN COUNT(DISTINCT DATE(ks.olcum_zamani)) < (SELECT CAST(ayar_degeri AS UNSIGNED) FROM sistem_ayarlari WHERE ayar_anahtari = 'minimum_gunluk_olcum') THEN 'Ölçüm Eksikliği'
                    WHEN IFNULL(hus.genel_uyum_skoru, 0) < 50 THEN 'Düşük Uyum'
                    ELSE 'Stabil'
                END AS durum_kategorisi
            FROM hastalar h
            JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id
            LEFT JOIN kan_sekeri_olcumleri ks ON h.hasta_id = ks.hasta_id
                AND DATE(ks.olcum_zamani) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                AND ks.gecerli_olcum = TRUE
            LEFT JOIN uyarilar u ON h.hasta_id = u.hasta_id
                AND u.uyari_tarihi >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            LEFT JOIN uyari_turleri ut ON u.uyari_turu_id = ut.uyari_turu_id
            LEFT JOIN hasta_uyum_skorlari hus ON h.hasta_id = hus.hasta_id
                AND hus.hesaplama_tarihi = CURDATE()
            WHERE k.aktif_durum = TRUE
            GROUP BY h.hasta_id, k.ad, k.soyad, h.doktor_id, IFNULL(hus.genel_uyum_skoru, 0)
            HAVING durum_kategorisi != 'Stabil' OR kritik_uyari_sayisi > 0
            ORDER BY FIELD(durum_kategorisi, 'Kritik Durum (Kan Şekeri)', 'Ölçüm Eksikliği', 'Düşük Uyum', 'Stabil'), son_7_gun_ortalama_kan_sekeri DESC;
            """,
            """
            DROP INDEX IF EXISTS idx_kan_sekeri_performans ON kan_sekeri_olcumleri;
            """,
            """
            CREATE INDEX idx_kan_sekeri_performans ON kan_sekeri_olcumleri(hasta_id, olcum_tarihi, kan_sekeri_degeri, gecerli_olcum);
            """,
            """
            DROP INDEX IF EXISTS idx_diyet_takip_performans ON diyet_takibi;
            """,
            """
            CREATE INDEX idx_diyet_takip_performans ON diyet_takibi(hasta_id, takip_tarihi, diyet_uygulandimi);
            """,
            """
            DROP INDEX IF EXISTS idx_egzersiz_takip_performans ON egzersiz_takibi;
            """,
            """
            CREATE INDEX idx_egzersiz_takip_performans ON egzersiz_takibi(hasta_id, takip_tarihi, egzersiz_yapildimi);
            """,
            """
            DROP INDEX IF EXISTS idx_uyari_doktor_tarih_okundu ON uyarilar;
            """,
            """
            CREATE INDEX idx_uyari_doktor_tarih_okundu ON uyarilar(doktor_id, uyari_tarihi, okundu);
            """,
            """
            SET GLOBAL event_scheduler = ON;
            """,
            """
            DROP EVENT IF EXISTS event_gunluk_olcum_kontrol;
            """,
            """
            CREATE EVENT event_gunluk_olcum_kontrol
            ON SCHEDULE EVERY 1 DAY
            STARTS (CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 5 MINUTE)
            DO
            BEGIN
                CALL gunluk_olcum_kontrol_ve_uyari();
            END;
            """,
            """
            DROP EVENT IF EXISTS event_gunluk_uyum_skoru_hesapla;
            """,
            """
            CREATE EVENT event_gunluk_uyum_skoru_hesapla
            ON SCHEDULE EVERY 1 DAY
            STARTS (CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 10 MINUTE)
            DO
            BEGIN
                DECLARE done INT DEFAULT FALSE;
                DECLARE hasta_id_var INT;

                DECLARE hasta_cursor CURSOR FOR
                    SELECT hasta_id FROM hastalar;

                DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

                OPEN hasta_cursor;

                hasta_loop: LOOP
                    FETCH hasta_cursor INTO hasta_id_var;
                    IF done THEN
                        LEAVE hasta_loop;
                    END IF;
                    CALL hasta_uyum_skoru_hesapla(hasta_id_var, CURDATE() - INTERVAL 1 DAY);
                END LOOP;

                CLOSE hasta_cursor;
            END;
            """,
            """
            DROP EVENT IF EXISTS event_gunluk_kan_sekeri_istatistikleri;
            """,
            """
            CREATE EVENT event_gunluk_kan_sekeri_istatistikleri
            ON SCHEDULE EVERY 1 DAY
            STARTS (CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 15 MINUTE)
            DO
            BEGIN
                DECLARE done INT DEFAULT FALSE;
                DECLARE hasta_id_var INT;

                DECLARE hasta_cursor CURSOR FOR
                    SELECT hasta_id FROM hastalar;

                DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

                OPEN hasta_cursor;

                hasta_loop: LOOP
                    FETCH hasta_cursor INTO hasta_id_var;
                    IF done THEN
                        LEAVE hasta_loop;
                    END IF;
                    CALL gunluk_istatistik_hesapla(hasta_id_var, CURDATE() - INTERVAL 1 DAY);
                END LOOP;

                CLOSE hasta_cursor;
            END;
            """
        ]

        for sql_command in tables_sql:
            cursor.execute(sql_command)
            conn.commit()

        print("Veritabanı tabloları, triggerlar, fonksiyonlar ve prosedürler kontrol edildi/oluşturuldu.")

        initial_data_insert(cursor)

        conn.commit()
        print("Veritabanı kurulumu ve başlangıç verisi ekleme tamamlandı.")

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        messagebox.showerror("Veritabanı Başlatma Hatası", f"Veritabanı ve tablolar oluşturulurken hata oluştu:\n{err}\n"
                                                          f"Lütfen MySQL sunucusunun doğru çalıştığından ve şifrelerin eşleştiğinden emin olun.")
        print(f"Veritabanı başlatma hatası: {err}")
    except Exception as e:
        if conn: conn.rollback()
        messagebox.showerror("Genel Hata", f"Uygulama başlatılırken beklenmeyen bir hata oluştu: {e}")
        print(f"Genel başlatma hatası: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def initial_data_insert(cursor):
    conn = cursor.connection

    try:
        print("Initial data insert started.")

        cursor.execute("INSERT IGNORE INTO kullanici_rolleri (rol_adi) VALUES ('Doktor'), ('Hasta')")
        conn.commit()

        uyari_turleri = [
            ('Acil Uyarı', 'Hastanın kan şekeri seviyesi kritik seviyelerin altına düştü. Hipoglisemi riski! Hızlı müdahale gerekebilir.', 'Kritik'),
            ('Takip Uyarısı', 'Hastanın kan şekeri orta yüksek seviyede. Durum izlenmeli.', 'Orta'),
            ('İzleme Uyarısı', 'Hastanın kan şekeri yüksek seviyede. Diyabet kontrolü gereklidir.', 'Yüksek'),
            ('Acil Müdahale Uyarısı', 'Hastanın kan şekeri kritik seviyelerin üzerinde. Hiperglisemi durumu. Acil müdahale gerekebilir.', 'Kritik'),
            ('Ölçüm Eksik Uyarısı', 'Hasta gün boyunca kan şekeri ölçümü yapmamıştır. Acil takip önerilir.', 'Yüksek'),
            ('Ölçüm Yetersiz Uyarısı', 'Hastanın günlük kan şekeri ölçüm sayısı yetersizdir (<3). Durum izlenmelidir.', 'Orta')
        ]
        for uyari_adi, aciklama, aciliyet in uyari_turleri:
            cursor.execute("INSERT IGNORE INTO uyari_turleri (uyari_adi, aciklama, aciliyet_seviyesi) VALUES (%s, %s, %s)",
                           (uyari_adi, aciklama, aciliyet))
        conn.commit()

        diyet_turleri = [
            ('Az Şekerli Diyet', 'Şekerli gıdalar sınırlanır, kompleks karbonhidratlara öncelik verilir. Lifli gıdalar ve düşük glisemik indeksli besinler tercih edilir.'),
            ('Şekersiz Diyet', 'Rafine şeker ve şeker katkılı tüm ürünler tamamen dışlanır. Hiperglisemi riski taşıyan bireylerde önerilir.'),
            ('Dengeli Beslenme', 'Diyabetli bireylerin yaşam tarzına uygun, dengeli ve sürdürülebilir bir diyet yaklaşımıdır. Tüm besin gruplarından yeterli miktarda alınır; porsiyon kontrolü, mevsimsel taze ürünler ve su tüketimi temel unsurlardır.')
        ]
        for diyet_adi, aciklama in diyet_turleri:
            cursor.execute("INSERT IGNORE INTO diyet_turleri (diyet_adi, aciklama) VALUES (%s, %s)", (diyet_adi, aciklama))
        conn.commit()

        egzersiz_turleri = [
            ('Yürüyüş', 'Hafif tempolu, günlük yapılabilecek bir egzersizdir.'),
            ('Bisiklet', 'Alt vücut kaslarını çalıştırır ve dış mekanda veya sabit bisikletle uygulanabilir.'),
            ('Klinik Egzersiz', 'Doktor tarafından verilen belirli hareketleri içeren planlı egzersizlerdir. Stresi azaltılması ve hareket kabiliyetinin artırılması amaçlanır.')
        ]
        for egzersiz_adi, aciklama in egzersiz_turleri:
            cursor.execute("INSERT IGNORE INTO egzersiz_turleri (egzersiz_adi, aciklama) VALUES (%s, %s)", (egzersiz_adi, aciklama))
        conn.commit()

        belirtiler = [
            ('Poliüri', 'Sık idrara çıkma'), ('Polifaji', 'Aşırı açlık hissi'), ('Polidipsi', 'Aşırı susama hissi'),
            ('Nöropati', 'El ve ayaklarda karıncalanma veya uyuşma hissi'), ('Kilo kaybı', 'Ani kilo kaybı'),
            ('Yorgunluk', 'Sürekli yorgunluk hissi'), ('Yaraların yavaş iyileşmesi', 'Yaraların normal sürede iyileşmemesi'),
            ('Bulanık görme', 'Görme bozukluğu')
        ]
        for belirti_adi, aciklama in belirtiler:
            cursor.execute("INSERT IGNORE INTO belirtiler (belirti_adi, aciklama) VALUES (%s, %s)", (belirti_adi, aciklama))
        conn.commit()

        sistem_ayarlari = [
            ('olcum_hatirlatma_saatleri', '["07:00", "12:00", "15:00", "18:00", "22:00"]', 'Kan şekeri ölçüm hatırlatma saatleri', 'json'),
            ('hipoglisemi_esik', '70', 'Hipoglisemi uyarı eşiği (mg/dL)', 'number'),
            ('hiperglisemi_esik', '200', 'Hiperglisemi uyarı eşiği (mg/dL)', 'number'),
            ('minimum_gunluk_olcum', '3', 'Minimum günlük ölçüm sayısı', 'number'),
            ('sifre_gecerlilik_suresi', '90', 'Şifre geçerlilik süresi (gün)', 'number'),
            ('oturum_zaman_asimi', '30', 'Oturum zaman aşımı (dakika)', 'number')
        ]
        for ayar_anahtari, ayar_degeri, aciklama, veri_tipi in sistem_ayarlari:
            cursor.execute("INSERT IGNORE INTO sistem_ayarlari (ayar_anahtari, ayar_degeri, aciklama, veri_tipi) VALUES (%s, %s, %s, %s)",
                           (ayar_anahtari, ayar_degeri, aciklama, veri_tipi))
        conn.commit()

        rules_data = [
            (0, 69.99, '["Nöropati", "Polifaji", "Yorgunluk"]', 'Dengeli Beslenme', None),
            (0, 69.99, '["Yorgunluk", "Kilo kaybı"]', 'Az Şekerli Diyet', 'Yürüyüş'),
            (70, 110, '["Polifaji", "Polidipsi"]', 'Dengeli Beslenme', 'Yürüyüş'),
            (70, 110, '["Bulanık görme", "Nöropati"]', 'Az Şekerli Diyet', 'Klinik Egzersiz'),
            (70, 110, '["Poliüri", "Polidipsi"]', 'Şekersiz Diyet', 'Klinik Egzersiz'),
            (110.01, 180, '["Yorgunluk", "Nöropati", "Bulanık görme"]', 'Az Şekerli Diyet', 'Yürüyüş'),
            (110.01, 180, '["Yaraların yavaş iyileşmesi", "Polifaji", "Polidipsi"]', 'Şekersiz Diyet', 'Klinik Egzersiz'),
            (180.01, 999.99, '["Yaraların yavaş iyileşmesi", "Kilo kaybı"]', 'Şekersiz Diyet', 'Yürüyüş')
        ]
        for ks_min, ks_max, belirtiler_json, diyet_adi, egzersiz_adi in rules_data:
            diyet_id = None
            egzersiz_id = None
            cursor.execute("SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = %s", (diyet_adi,))
            diyet_id_result = cursor.fetchone()
            if diyet_id_result: diyet_id = diyet_id_result[0]

            if egzersiz_adi:
                cursor.execute("SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = %s", (egzersiz_adi,))
                egzersiz_id_result = cursor.fetchone()
                if egzersiz_id_result: egzersiz_id = egzersiz_id_result[0]

            cursor.execute("""
                INSERT IGNORE INTO kural_tabani (kan_sekeri_min, kan_sekeri_max, belirtiler, onerilen_diyet_id, onerilen_egzersiz_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (ks_min, ks_max, belirtiler_json, diyet_id, egzersiz_id))
        conn.commit()

        doctor_plain_password = 'doktor123' 
        cursor.execute("""
            INSERT IGNORE INTO kullanicilar
            (tc_kimlik_no, ad, soyad, eposta, sifre, dogum_tarihi, cinsiyet, rol_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, (SELECT rol_id FROM kullanici_rolleri WHERE rol_adi = 'Doktor'))
        """, ('11111111111', 'Dr. Ahmet', 'Yılmaz', 'ahmet.yilmaz@ornek.com', doctor_plain_password, '1980-01-01', 'Erkek'))
        conn.commit()

        cursor.execute("""
            INSERT IGNORE INTO doktorlar (kullanici_id, uzmanlik_alani, diploma_no)
            SELECT kullanici_id, 'Endokrinoloji', 'DIP001' FROM kullanicilar WHERE tc_kimlik_no = '11111111111'
        """)
        conn.commit()

        patient_plain_password = 'hasta123'
        cursor.execute("""
            INSERT IGNORE INTO kullanicilar
            (tc_kimlik_no, ad, soyad, eposta, sifre, dogum_tarihi, cinsiyet, rol_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, (SELECT rol_id FROM kullanici_rolleri WHERE rol_adi = 'Hasta'))
        """, ('22222222222', 'Mehmet', 'Demir', 'mehmet.demir@ornek.com', patient_plain_password, '1990-05-15', 'Erkek'))
        conn.commit()

        cursor.execute("""
            INSERT IGNORE INTO hastalar (kullanici_id, doktor_id, tani_tarihi, diyabet_tipi)
            SELECT
                k.kullanici_id,
                (SELECT doktor_id FROM doktorlar d JOIN kullanicilar dk ON d.kullanici_id = dk.kullanici_id WHERE dk.tc_kimlik_no = '11111111111'),
                '2024-01-15',
                'Tip 2'
            FROM kullanicilar k
            WHERE k.tc_kimlik_no = '22222222222'
        """)
        conn.commit()

        cursor.execute("""
            INSERT IGNORE INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi, siddet_seviyesi, notlar)
            VALUES (
                (SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '22222222222'),
                (SELECT belirti_id FROM belirtiler WHERE belirti_adi = 'Yorgunluk'),
                CURDATE(),
                'Orta',
                'Bugün biraz daha yorgun hissediyor.'
            )
        """)
        conn.commit()

        cursor.execute("""
            INSERT IGNORE INTO hasta_belirtileri (hasta_id, belirti_id, kayit_tarihi, siddet_seviyesi, notlar)
            VALUES (
                (SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '22222222222'),
                (SELECT belirti_id FROM belirtiler WHERE belirti_adi = 'Polifaji'),
                CURDATE() - INTERVAL 1 DAY,
                'Hafif',
                'Dün akşam hafif açlık hissi vardı.'
            )
        """)
        conn.commit()

        cursor.execute("""
            INSERT IGNORE INTO diyet_planlari (hasta_id, doktor_id, diyet_turu_id, baslangic_tarihi, aktif_durum)
            SELECT
                (SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '22222222222'),
                (SELECT doktor_id FROM doktorlar d JOIN kullanicilar k ON d.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '11111111111'),
                (SELECT diyet_turu_id FROM diyet_turleri WHERE diyet_adi = 'Az Şekerli Diyet'),
                CURDATE() - INTERVAL 7 DAY,
                TRUE
        """)
        conn.commit()

        cursor.execute("""
            INSERT IGNORE INTO egzersiz_planlari (hasta_id, doktor_id, egzersiz_turu_id, baslangic_tarihi, aktif_durum)
            SELECT
                (SELECT hasta_id FROM hastalar h JOIN kullanicilar k ON h.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '22222222222'),
                (SELECT doktor_id FROM doktorlar d JOIN kullanicilar k ON d.kullanici_id = k.kullanici_id WHERE k.tc_kimlik_no = '11111111111'),
                (SELECT egzersiz_turu_id FROM egzersiz_turleri WHERE egzersiz_adi = 'Yürüyüş'),
                CURDATE() - INTERVAL 7 DAY,
                TRUE
        """)
        conn.commit()

        print("Initial data insert completed.")

    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno != 1062:
            messagebox.showerror("Veritabanı Hatası", f"Başlangıç verileri eklenirken hata oluştu: {err}")
        else:
            print(f"Uyarı: Veritabanına zaten mevcut girişler eklenmeye çalışıldı: {err}")
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Hata", f"Başlangıç verileri eklenirken beklenmeyen bir hata oluştu: {e}")


def main():
    global main_window

    create_database_and_tables()

    main_window = tk.Tk()
    main_window.resizable(False, False)

    main_window.protocol("WM_DELETE_WINDOW", lambda: (main_window.quit(), main_window.destroy()))

    show_login_screen()

    main_window.mainloop()

if __name__ == "__main__":
    main()
