import flet as ft
import re
import urllib.parse
import os
import requests

class LocationProcessor:
    def expand_short_url(self, url):
        """Rozbalení zkrácených URL (goo.gl, maps.app.goo.gl)"""
        try:
            if 'goo.gl' in url or 'maps.app.goo.gl' in url:
                # Následování redirectů pro získání plné URL
                response = requests.head(url, allow_redirects=True, timeout=10)
                return response.url
            return url
        except Exception as e:
            print(f"Chyba při rozbalování URL: {e}")
            return url
    
    def extract_coordinates(self, url):
        """Extrakce GPS souřadnic z Google Maps URL"""
        # Nejdřív zkus rozbalit zkrácené URL
        expanded_url = self.expand_short_url(url)
        
        # Dekódování URL
        decoded_url = urllib.parse.unquote(expanded_url)
        
        print(f"Původní URL: {url}")
        print(f"Rozbalená URL: {expanded_url}")
        print(f"Dekódovaná URL: {decoded_url}")
        
        # Různé formáty Google Maps URL
        patterns = [
            # Standardní @lat,lng,zoom
            r'@(-?\d+\.?\d*),(-?\d+\.?\d*),\d+',
            # /lat,lng/ formát
            r'/(-?\d+\.?\d*),(-?\d+\.?\d*)/',
            # ?q=lat,lng
            r'q=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            # ll=lat,lng (query parameter)
            r'll=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            # center=lat,lng
            r'center=(-?\d+\.?\d*),(-?\d+\.?\d*)',
            # coordinates v URL path
            r'maps/place/[^/]*/@(-?\d+\.?\d*),(-?\d+\.?\d*)',
            # data coordinates v URL
            r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)',
            # další možný formát
            r'coordinates=(-?\d+\.?\d*),(-?\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, decoded_url)
            if match:
                try:
                    lat = float(match.group(1))
                    lng = float(match.group(2))
                    # Kontrola platných souřadnic
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        print(f"Nalezeny souřadnice: {lat}, {lng}")
                        return lat, lng
                except (ValueError, IndexError):
                    continue
        
        # Pokud nic nenašlo, pokus o extrakci z jakékoliv části URL
        # Hledání jakýchkoliv dvou čísel oddělených čárkou
        number_pattern = r'(-?\d+\.?\d+),(-?\d+\.?\d+)'
        matches = re.findall(number_pattern, decoded_url)
        
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
        # Nejdřív zkus rozbalit zkrácené URL
        expanded_url = self.expand_short_url(url)
        decoded_url = urllib.parse.unquote(expanded_url)
        
        patterns = [
            # /place/Název
            r'/place/([^/@]+)',
            # q=Název (před souřadnicemi)
            r'q=([^&@,]+)',
            # search/Název
            r'search/([^/]+)',
            # data v URL
            r'data=.*?([A-Za-z\s]+).*?@'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, decoded_url)
            if match:
                name = match.group(1)
                # Čištění názvu
                name = name.replace('+', ' ').replace('%20', ' ').replace('%2C', ', ')
                # Odstranění souřadnic z názvu
                name = re.sub(r'[-+]?\d*\.?\d+,[-+]?\d*\.?\d+', '', name).strip()
                # Odstranění speciálních znaků na konci
                name = re.sub(r'[/@]+$', '', name).strip()
                if name and len(name) > 2 and not name.replace(',', '').replace('.', '').replace('-', '').replace(' ', '').isdigit():
                    return name
        
        return None

def main(page: ft.Page):
    page.title = "GPS Lokace z Google Maps"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 600
    
    # UI komponenty
    title = ft.Text("GPS Lokace z Google Maps", size=20, weight=ft.FontWeight.BOLD)
    
    url_input = ft.TextField(
        label="URL z Google Maps",
        hint_text="Vložte odkaz nebo použijte Sdílet...",
        multiline=False,
        expand=True
    )
    
    name_result = ft.Text("Název: -", selectable=True)
    coords_result = ft.Text("Souřadnice: -", selectable=True)
    address_result = ft.Text("Adresa: -", selectable=True)
    
    # Intent handler pro Android
    def on_route_change(e):
        """Zpracování intent dat z Androidu"""
        if page.route.startswith("/share"):
            # Extrakce URL z route
            shared_url = page.route.replace("/share/", "").replace("/share", "")
            if shared_url:
                url_input.value = urllib.parse.unquote(shared_url)
                process_location(None)
                name_result.value += ' (Ze sdílení)'
                page.update()
    
    page.on_route_change = on_route_change
    
    def process_location(e):
        """Zpracování URL z Google Maps"""
        url = url_input.value.strip()
        
        if not url:
            show_error("Vložte prosím URL odkaz")
            return
            
        try:
            # Vytvoř instanci pro použití metod
            processor = LocationProcessor()
            coords = processor.extract_coordinates(url)
            
            if coords:
                lat, lng = coords
                coords_result.value = f'Souřadnice: {lat:.6f}, {lng:.6f}'
                
                name = processor.extract_place_name(url)
                if name:
                    name_result.value = f'Název: {name}'
                else:
                    name_result.value = 'Název: Neznámá lokace'
                
                address_result.value = f'Zeměpisná šířka: {lat:.6f}°\nZeměpisná délka: {lng:.6f}°'
                
            else:
                show_error("Nepodařilo se extrahovat souřadnice z URL")
                
        except Exception as ex:
            show_error(f"Chyba při zpracování: {str(ex)}")
        
        page.update()
    
    def show_error(message):
        """Zobrazení chybové zprávy"""
        name_result.value = f'Chyba: {message}'
        coords_result.value = 'Souřadnice: -'
        address_result.value = 'Adresa: -'
    
    def clear_data(e):
        """Vymazání všech dat"""
        url_input.value = ''
        name_result.value = 'Název: -'
        coords_result.value = 'Souřadnice: -'
        address_result.value = 'Adresa: -'
        page.update()
    
    def check_shared_url():
        """Kontrola sdíleného URL při spuštění"""
        try:
            shared_url_file = os.path.join(os.getcwd(), 'shared_url.txt')
            
            if os.path.exists(shared_url_file):
                with open(shared_url_file, 'r') as f:
                    shared_url = f.read().strip()
                
                if shared_url:
                    url_input.value = shared_url
                    process_location(None)
                    name_result.value += ' (Automaticky ze sdílení)'
                
                os.remove(shared_url_file)
                page.update()
                
        except Exception as e:
            print(f"Chyba při kontrole sdíleného URL: {e}")
    
    # Tlačítka
    process_btn = ft.ElevatedButton(
        "Analyzovat lokaci",
        on_click=process_location,
        width=200
    )
    
    clear_btn = ft.OutlinedButton(
        "Vymazat",
        on_click=clear_data,
        width=200
    )
    
    # Layout
    page.add(
        ft.Container(
            ft.Column([
                title,
                ft.Divider(),
                url_input,
                ft.Row([process_btn], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                name_result,
                coords_result,
                address_result,
                ft.Divider(),
                ft.Row([clear_btn], alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=10),
            padding=20
        )
    )
    
    # Kontrola sdíleného URL při spuštění
    check_shared_url()

if __name__ == "__main__":
    ft.app(target=main)