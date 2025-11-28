from kerykeion import AstrologicalSubject

class AstroCalculator:
    """星盘计算器"""
    
    def calculate_birth_chart(self, birth_data):
        """
        计算星盘
        birth_data = {
            'name': 'User',
            'year': 1990,
            'month': 5,
            'day': 15,
            'hour': 14,
            'minute': 30,
            'city': 'New York',
            'nation': 'US'
        }
        """
        try:
            # 创建星盘对象
            person = AstrologicalSubject(
                birth_data.get('name', 'User'),
                birth_data['year'],
                birth_data['month'],
                birth_data['day'],
                birth_data['hour'],
                birth_data['minute'],
                birth_data['city'],
                birth_data.get('nation', 'US')
            )
            
            # 提取关键数据
            chart_data = {
                'sun': {
                    'sign': person.sun['sign'],
                    'degree': round(person.sun['position'], 2),
                    'house': person.sun.get('house', 'Unknown')
                },
                'moon': {
                    'sign': person.moon['sign'],
                    'degree': round(person.moon['position'], 2),
                    'house': person.moon.get('house', 'Unknown')
                },
                'venus': {
                    'sign': person.venus['sign'],
                    'degree': round(person.venus['position'], 2),
                    'house': person.venus.get('house', 'Unknown')
                },
                'mars': {
                    'sign': person.mars['sign'],
                    'degree': round(person.mars['position'], 2),
                    'house': person.mars.get('house', 'Unknown')
                },
                'mercury': {
                    'sign': person.mercury['sign'],
                    'degree': round(person.mercury['position'], 2)
                },
                'jupiter': {
                    'sign': person.jupiter['sign'],
                    'degree': round(person.jupiter['position'], 2)
                },
                'rising': {
                    'sign': person.first_house['sign'],
                    'degree': round(person.first_house['position'], 2)
                },
                'house7': {
                    'sign': person.seventh_house['sign'],
                    'degree': round(person.seventh_house['position'], 2)
                }
            }
            
            return chart_data
            
        except Exception as e:
            raise Exception(f"Birth chart calculation failed: {str(e)}")