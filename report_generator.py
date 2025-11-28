import openai
import os

class ReportGenerator:
    """使用ChatGPT和DALL-E生成占星报告"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key
    
    def generate_full_report_with_image(self, chart_data, gender='female'):
        """
        生成完整报告（文字 + 图片）
        """
        # 1. 生成文字报告
        text_report = self._generate_text_report(chart_data, gender)
        
        # 2. 生成AI图片
        image_url = self._generate_soulmate_image(
            text_report['soulmate_appearance'], 
            gender
        )
        
        return {
            **text_report,
            'hd_image_url': image_url,
            'blur_image_url': image_url  # V1简化：前端CSS处理模糊
        }
    
    def _generate_text_report(self, chart_data, gender):
        """生成文字报告"""
        prompt = self._build_prompt(chart_data, gender)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional astrologer specializing in soulmate readings.
Your style:
- Specific and detailed (not vague)
- Warm and empathetic
- Mystical but modern
- Focus on actionable insights

IMPORTANT: Output in English only."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
            
        except Exception as e:
            raise Exception(f"AI report generation failed: {str(e)}")
    
    def _build_prompt(self, chart_data, gender):
        """构建prompt"""
        partner_pronoun = "he" if gender == 'female' else "she"
        
        return f"""Based on this birth chart, create a detailed soulmate profile.

Chart Data:
- Sun in {chart_data['sun']['sign']} (House {chart_data['sun']['house']})
- Moon in {chart_data['moon']['sign']} (House {chart_data['moon']['house']})
- Venus in {chart_data['venus']['sign']} (House {chart_data['venus']['house']})
- Mars in {chart_data['mars']['sign']}
- Rising in {chart_data['rising']['sign']}
- 7th House in {chart_data['house7']['sign']}

User gender: {gender}

Generate a soulmate profile in this EXACT format:

## PERSONALITY_ANALYSIS ##
(2-3 sentences about their love style and emotional needs)

## LOVE_APPROACH ##
(3-4 sentences about how they express love and what they seek)

## SOULMATE_APPEARANCE ##
(4-5 sentences with specific physical details: height, build, eyes, hair, style, overall vibe)

## SOULMATE_PERSONALITY ##
(5-6 specific personality traits with brief explanations)

## SOULMATE_CAREER ##
(List 4-5 specific career fields or job types)

## MEETING_PLACES ##
(List 5-6 specific places or scenarios where they might meet)

## BEST_TIMING ##
(Identify 2-3 months in 2025 with brief astrological reasoning)

## COMPATIBILITY_TIPS ##
(3-4 specific tips for building a lasting connection)

Requirements:
- Be SPECIFIC (not "tall" but "5'10\"-6'1\"")
- Avoid generic advice
- Make it feel personal and unique
- Use vivid, concrete language
- All content in English"""
    
    def _parse_response(self, content):
        """解析GPT回复"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('##') and line.endswith('##'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                current_section = line.replace('#', '').strip().lower().replace(' ', '_')
                current_content = []
            else:
                if line:
                    current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return {
            'personality_analysis': sections.get('personality_analysis', ''),
            'love_approach': sections.get('love_approach', ''),
            'soulmate_appearance': sections.get('soulmate_appearance', ''),
            'soulmate_personality': sections.get('soulmate_personality', ''),
            'soulmate_career': sections.get('soulmate_career', ''),
            'meeting_places': sections.get('meeting_places', ''),
            'best_timing': sections.get('best_timing', ''),
            'compatibility_tips': sections.get('compatibility_tips', '')
        }
    
    def _generate_soulmate_image(self, appearance_description, gender):
        """使用DALL-E生成图片"""
        if gender == 'female':
            base_prompt = "Portrait photo of an attractive man, "
        else:
            base_prompt = "Portrait photo of an attractive woman, "
        
        # 提取关键外貌特征
        key_features = appearance_description[:200]  # 取前200字符
        
        full_prompt = f"""{base_prompt}{key_features}
Professional photography, natural lighting, warm genuine smile,
looking at camera, soft bokeh background, cinematic quality,
intimate atmosphere, 35mm lens, photo-realistic"""
        
        try:
            response = openai.Image.create(
                model="dall-e-3",
                prompt=full_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            return response.data[0].url
            
        except Exception as e:
            # 如果失败，返回占位图
            print(f"Image generation failed: {str(e)}")
            return "https://via.placeholder.com/1024x1024?text=Soulmate+Portrait"
    
    def create_preview_from_full(self, full_data):
        """从完整报告创建预览版本"""
        return {
            'personality_analysis': full_data['personality_analysis'],
            'love_approach': full_data['love_approach'][:200] + "...",
            'soulmate_appearance': self._blur_text(full_data['soulmate_appearance']),
            'soulmate_personality': self._blur_text(full_data['soulmate_personality']),
            'soulmate_career': "███████ (Unlock to reveal)",
            'meeting_places': "███████ (Unlock to reveal)",
            'best_timing': "2025年██月 (Unlock to reveal)",
            'compatibility_tips': self._blur_text(full_data['compatibility_tips'], 0.3),
            'blur_image_url': full_data['blur_image_url']
        }
    
    def _blur_text(self, text, keep_ratio=0.4):
        """部分模糊文本"""
        if not text:
            return "███ (Unlock to reveal)"
        
        words = text.split()
        keep_count = max(3, int(len(words) * keep_ratio))
        
        visible = ' '.join(words[:keep_count])
        return f"{visible} ███████ (Unlock to reveal)"