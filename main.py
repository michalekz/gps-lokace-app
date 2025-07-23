from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
import re
import urllib.parse
import os
import requests


class LocationProcessor:
    def expand_short_url(self, url):
        """Rozbalení zkrácených URL (goo.gl, maps.app.goo.gl, mapy.cz/s/)"""
        try:
            if 'goo.gl' in url or 'maps.app.goo.gl' in url or 'mapy.cz/s/' in url or 'mapy.com/s/' in url:
                response = requests.head(url, allow_redirects=True, timeout=10)
                return response.url
            return url
        except Exception as e:
            print(f"Chyba při rozbalování URL: {e}")
            return url

    def extract_coordinates(self, url):
        """Extrakce GPS souřadnic z Google Maps a Mapy.cz URL"""
        expanded_url = self.expand_short_url(url)
        decoded_url = urllib.parse.unquote(expanded_url)
        
        print(f"Původní URL: {url}")
        print(f"Rozbalená URL: {expanded_url}")
        print(f"Dekódovaná URL: {decoded_url}")
        
        if 'mapy.cz' in decoded_url or 'mapy.com' in decoded_url:
            return self.extract_mapy_cz_coordinates(decoded_url)
        else:
            return self.extract_google_maps_coordinates(decoded_url)

    def extract_mapy_cz_coordinates(self, url):
        """Extrakce souřadnic z Mapy.cz URL"""
        print("Parsování Mapy.cz URL...")
        
        patterns = [
            r'[&?]x=([0-9.-]+)[&]y=([0-9.-]+)',
            r'[&?]query=([0-9.-]+)[,\s]+([0-9.-]+)',
            r'[&?]center=([0-9.-]+)[,\s]+([0-9.-]+)',
            r'/misto/([0-9.-]+),([0-9.-]+)',
            r'#.*?([0-9.-]+),([0-9.-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    lng = float(match.group(1))
                    lat = float(match.group(2))
                    
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        print(f"Nalezeny souřadnice Mapy.cz: {lat}, {lng}")
                        return lat, lng
                except (ValueError, IndexError):
                    continue
        
        number_pattern = r'([0-9]+\.[0-9]+),([0-9]+\.[0-9]+)'
        matches = re.findall(number_pattern, url)
        
        for match in matches:
            try:
                num1, num2 = float(match[0]), float(match[1])
                
                if -90 <= num1 <= 90 and -180 <= num2 <= 180:
                    print(f"Nalezeny souřadnice (lat,lng): {num1}, {num2}")
                    return num1, num2
                elif -90 <= num2 <= 90 and -180 <= num1 <= 180:
                    print(f"Nalezeny souřadnice (lng,lat): {num2}, {num1}")
                    return num2, num1
            except ValueError:
                continue
                
        return None

    def extract_google_maps_coordinates(self, url):
        """Extrakce souřadnic z Google Maps URL"""
        print("Parsování Google Maps URL...")
        
        patterns = [
            r'@(-?\d+\.?\d*),(-?\d+\.?\d*),\d+',
            r'/(-?\d+\.?\d*),(-?\d+\.?\d*)/',
            r'q=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'll=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'center=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'maps/place/[^/]*/@(-?\d+\.?\d*),(-?\d+\.?\d*)',
            r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)',
            r'coordinates=(-?\d+\.?\d*),(-?\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                try:
                    lat = float(match.group(1))
                    lng = float(match.group(2))
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        print(f"Nalezeny souřadnice Google Maps: {lat}, {lng}")
                        return lat, lng
                except (ValueError, IndexError):
                    continue
        
        number_pattern = r'(-?\d+\.?\d+),(-?\d+\.?\d+)'
        matches = re.findall(number_pattern, url)
        
        for match in matches:
            try:
                lat = float(match[0])
                lng = float(match[1])
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    print(f"Nalezeny souřadnice (obecný pattern): {lat}, {lng}")
                    return lat, lng
            except ValueError:
                continue
        
        return None

    def extract_place_name(self, url):
        """Extrakce názvu místa z URL"""
        expanded_url = self.expand_short_url(url)
        decoded_url = urllib.parse.unquote(expanded_url)
        
        if 'mapy.cz' in decoded_url or 'mapy.com' in decoded_url:
            return self.extract_mapy_cz_place_name(decoded_url)
        else:
            return self.extract_google_maps_place_name(decoded_url)

    def extract_mapy_cz_place_name(self, url):
        """Extrakce názvu místa z Mapy.cz URL"""
        patterns = [
            r'[&?]q=([^&]+)',
            r'[&?]query=([^&]+)',
            r'/misto/([^/?]+)',
            r'/search/([^/?]+)',
            r'[&?]name=([^&]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                name = match.group(1)
                name = name.replace('+', ' ').replace('%20', ' ').replace('%2C', ', ')
                name = name.replace('-', ' ').strip()
                name = re.sub(r'[0-9]+\.[0-9]+[,\s]+[0-9]+\.[0-9]+', '', name).strip()
                
                if name and len(name) > 2 and not name.replace(',', '').replace('.', '').replace(' ', '').isdigit():
                    return name
        
        return None

    def extract_google_maps_place_name(self, url):
        """Extrakce názvu místa z Google Maps URL"""
        patterns = [
            r'/place/([^/@]+)',
            r'q=([^&@,]+)',
            r'search/([^/]+)',
            r'data=.*?([A-Za-z\s]+).*?@'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                name = match.group(1)
                name = name.replace('+', ' ').replace('%20', ' ').replace('%2C', ', ')
                name = re.sub(r'[-+]?\d*\.?\d+,[-+]?\d*\.?\d+', '', name).strip()
                name = re.sub(r'[/@]+$', '', name).strip()
                if name and len(name) > 2 and not name.replace(',', '').replace('.', '').replace('-', '').replace(' ', '').isdigit():
                    return name
        
        return None


class GPSLocationApp(App):
    def build(self):
        self.title = 'GPS Lokace z Map'
        
        # Hlavní layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Nadpis
        title_label = Label(
            text='GPS Lokace z Map',
            size_hint_y=None,
            height=50,
            font_size=20
        )
        main_layout.add_widget(title_label)
        
        # URL input
        self.url_input = TextInput(
            hint_text='Vložte odkaz z Google Maps nebo Mapy.cz...',
            size_hint_y=None,
            height=40,
            multiline=False
        )
        main_layout.add_widget(self.url_input)
        
        # Tlačítko pro analýzu
        analyze_btn = Button(
            text='Analyzovat lokaci',
            size_hint_y=None,
            height=50
        )
        analyze_btn.bind(on_press=self.analyze_location)
        main_layout.add_widget(analyze_btn)
        
        # Výsledky
        self.name_label = Label(
            text='Název: -',
            size_hint_y=None,
            height=30,
            text_size=(None, None),
            halign='left'
        )
        
        self.coords_label = Label(
            text='Souřadnice: -',
            size_hint_y=None,
            height=30,
            text_size=(None, None),
            halign='left'
        )
        
        self.address_label = Label(
            text='Adresa: -',
            size_hint_y=None,
            height=60,
            text_size=(None, None),
            halign='left'
        )
        
        main_layout.add_widget(self.name_label)
        main_layout.add_widget(self.coords_label)
        main_layout.add_widget(self.address_label)
        
        # Tlačítko pro vymazání
        clear_btn = Button(
            text='Vymazat',
            size_hint_y=None,
            height=40
        )
        clear_btn.bind(on_press=self.clear_data)
        main_layout.add_widget(clear_btn)
        
        # Kontrola sdíleného URL při spuštění
        Clock.schedule_once(self.check_shared_url, 0.5)
        
        return main_layout
    
    def analyze_location(self, instance):
        """Analýza URL"""
        url = self.url_input.text.strip()
        
        if not url:
            self.show_error("Vložte prosím URL odkaz")
            return
        
        try:
            processor = LocationProcessor()
            coords = processor.extract_coordinates(url)
            
            if coords:
                lat, lng = coords
                self.coords_label.text = f'Souřadnice: {lat:.6f}, {lng:.6f}'
                
                name = processor.extract_place_name(url)
                if name:
                    self.name_label.text = f'Název: {name}'
                else:
                    self.name_label.text = 'Název: Neznámá lokace'
                
                self.address_label.text = f'Zeměpisná šířka: {lat:.6f}°\nZeměpisná délka: {lng:.6f}°'
                
            else:
                self.show_error("Nepodařilo se extrahovat souřadnice z URL")
                
        except Exception as e:
            self.show_error(f"Chyba při zpracování: {str(e)}")
    
    def show_error(self, message):
        """Zobrazení chyby"""
        self.name_label.text = f'Chyba: {message}'
        self.coords_label.text = 'Souřadnice: -'
        self.address_label.text = 'Adresa: -'
    
    def clear_data(self, instance):
        """Vymazání dat"""
        self.url_input.text = ''
        self.name_label.text = 'Název: -'
        self.coords_label.text = 'Souřadnice: -'
        self.address_label.text = 'Adresa: -'
    
    def check_shared_url(self, dt):
        """Kontrola sdíleného URL při spuštění"""
        try:
            shared_url_file = '/data/data/org.test.gpslokace/files/shared_url.txt'
            
            if os.path.exists(shared_url_file):
                with open(shared_url_file, 'r') as f:
                    shared_url = f.read().strip()
                
                if shared_url:
                    self.url_input.text = shared_url
                    self.analyze_location(None)
                    self.name_label.text += ' (Ze sdílení)'
                
                os.remove(shared_url_file)
                
        except Exception as e:
            print(f"Chyba při kontrole sdíleného URL: {e}")


if __name__ == '__main__':
    GPSLocationApp().run()
