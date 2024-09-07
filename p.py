from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from instagrapi import Client
import re
import logging

app = FastAPI()

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credenciais do Instagram
IG_USERNAME = "karladojob"
IG_PASSWORD = "LUANLEVY17"

# Inicializa o cliente do Instagram e faz login
cl = Client()
cl.login(IG_USERNAME, IG_PASSWORD)

def extract_shortcode(url: str) -> str:
    """Extrai o shortcode da URL do Instagram."""
    logger.info(f"Extraindo shortcode da URL: {url}")
    
    # Regex para capturar o shortcode da URL
    match = re.search(r'/reel/([^/]+)/|/p/([^/]+)/', url)
    if match:
        shortcode = match.group(1) or match.group(2)
        logger.info(f"Shortcode extraído: {shortcode}")
        return shortcode
    raise ValueError("URL inválida.")

@app.get("/instagram/video")
async def get_video(url: str):
    try:
        logger.info(f"Recebido pedido para baixar vídeo: {url}")
        shortcode = extract_shortcode(url)
        logger.info(f"Obtendo informações da mídia para shortcode: {shortcode}")

        media_pk = cl.media_pk_from_code(shortcode)
        
        # Usar métodos públicos e privados para obter informações
        try:
            media = cl.media_info_gql(media_pk)
        except Exception as e:
            logger.error(f"Erro ao usar método gql: {e}")
            media = cl.media_info_v1(media_pk)
        
        if media is None:
            raise HTTPException(status_code=404, detail="Mídia não encontrada.")
        
        if media.media_type != 2:
            raise HTTPException(status_code=400, detail="A URL fornecida não é um vídeo.")
        
        file_path = cl.video_download(media_pk)
        logger.info(f"Caminho do arquivo baixado: {file_path}")
        
        return FileResponse(str(file_path), media_type='video/mp4', filename=file_path.name)
    except ValueError as e:
        logger.error(f"Erro ao extrair shortcode: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao baixar mídia: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor: " + str(e))

@app.get("/instagram/foto")
async def get_foto(url: str):
    try:
        logger.info(f"Recebido pedido para baixar foto: {url}")
        shortcode = extract_shortcode(url)
        logger.info(f"Obtendo informações da mídia para shortcode: {shortcode}")

        media_pk = cl.media_pk_from_code(shortcode)

        # Usar métodos públicos e privados para obter informações
        try:
            media = cl.media_info_gql(media_pk)
        except Exception as e:
            logger.error(f"Erro ao usar método gql: {e}")
            media = cl.media_info_v1(media_pk)

        if media is None:
            raise HTTPException(status_code=404, detail="Mídia não encontrada.")
        
        if media.media_type != 1:
            raise HTTPException(status_code=400, detail="A URL fornecida não é uma foto.")
        
        file_path = cl.photo_download(media_pk)
        logger.info(f"Caminho do arquivo baixado: {file_path}")
        
        return FileResponse(str(file_path), media_type='image/jpeg', filename=file_path.name)
    except ValueError as e:
        logger.error(f"Erro ao extrair shortcode: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao baixar mídia: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor: " + str(e))

@app.get("/instagram/istalk")
async def istalk(username: str):
    try:
        logger.info(f"Recebido pedido para informações do perfil: {username}")
        
        user_id = cl.user_id_from_username(username)
        user_info = cl.user_info(user_id)
        
        profile_data = {
            "username": user_info.username,
            "full_name": user_info.full_name,
            "bio": user_info.biography,
            "followers": user_info.follower_count,
            "following": user_info.following_count,
            "profile_pic_url": user_info.profile_pic_url_hd,
        }
        
        logger.info(f"Informações do perfil retornadas: {profile_data}")
        
        return JSONResponse(content=profile_data)
    except Exception as e:
        logger.error(f"Erro ao obter informações do perfil: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor: " + str(e))

@app.get("/instagram/story")
async def get_story(username: str):
    try:
        logger.info(f"Recebido pedido para baixar stories de: {username}")
        
        user_id = cl.user_id_from_username(username)
        stories = cl.user_stories(user_id)

        if not stories:
            raise HTTPException(status_code=404, detail="Nenhum story encontrado para este usuário.")

        # Supondo que queremos apenas o primeiro story de vídeo
        for story in stories:
            if story.media_type == 2:  # Tipo de mídia 2 é vídeo
                file_path = cl.story_download(story.pk)
                logger.info(f"Caminho do arquivo baixado: {file_path}")
                return FileResponse(str(file_path), media_type='video/mp4', filename=file_path.name)

        raise HTTPException(status_code=404, detail="Nenhum vídeo de story encontrado.")
    except Exception as e:
        logger.error(f"Erro ao baixar stories: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor: " + str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
