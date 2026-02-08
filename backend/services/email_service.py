import os
import asyncio
import logging
import resend
from dotenv import load_dotenv

load_dotenv()

# Configure Resend
resend.api_key = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, html_content: str) -> dict:
    """Send an email using Resend API"""
    params = {
        "from": SENDER_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    try:
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent successfully to {to_email}")
        return {"status": "success", "email_id": email.get("id")}
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")


async def send_verification_email(to_email: str, full_name: str, verification_token: str) -> dict:
    """Send email verification email"""
    verification_link = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="background: linear-gradient(90deg, #7C3AED, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">MyDar</h1>
        </div>
        
        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; margin-bottom: 20px;">
            <h2 style="color: #1f2937; margin-top: 0;">Bienvenue, {full_name} ! 👋</h2>
            <p>Merci de vous être inscrit sur Smart Life. Pour activer votre compte, veuillez confirmer votre adresse email en cliquant sur le bouton ci-dessous :</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" style="display: inline-block; background: linear-gradient(90deg, #8B5CF6, #06B6D4, #22C55E); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">Confirmer mon email</a>
            </div>
            
            <p style="color: #6b7280; font-size: 14px;">Ou copiez ce lien dans votre navigateur :</p>
            <p style="background-color: #e5e7eb; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">{verification_link}</p>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 20px;">Ce lien expire dans 24 heures.</p>
        </div>
        
        <div style="text-align: center; color: #6b7280; font-size: 12px;">
            <p>Si vous n'avez pas créé de compte sur Smart Life, ignorez simplement cet email.</p>
            <p style="margin-top: 20px;">© 2025 MyDar - Smart Home</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(to_email, "Confirmez votre adresse email - MyDar", html_content)


async def send_password_reset_email(to_email: str, full_name: str, reset_token: str) -> dict:
    """Send password reset email"""
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="background: linear-gradient(90deg, #7C3AED, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">MyDar</h1>
        </div>
        
        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; margin-bottom: 20px;">
            <h2 style="color: #1f2937; margin-top: 0;">Réinitialisation de mot de passe 🔐</h2>
            <p>Bonjour {full_name},</p>
            <p>Vous avez demandé la réinitialisation de votre mot de passe. Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="display: inline-block; background: linear-gradient(90deg, #7C3AED, #06B6D4); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">Réinitialiser mon mot de passe</a>
            </div>
            
            <p style="color: #6b7280; font-size: 14px;">Ou copiez ce lien dans votre navigateur :</p>
            <p style="background-color: #e5e7eb; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">{reset_link}</p>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 20px;">Ce lien expire dans 1 heure.</p>
        </div>
        
        <div style="text-align: center; color: #6b7280; font-size: 12px;">
            <p>Si vous n'avez pas demandé cette réinitialisation, ignorez simplement cet email. Votre mot de passe restera inchangé.</p>
            <p style="margin-top: 20px;">© 2025 MyDar - Smart Home</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(to_email, "Réinitialisation de mot de passe - MyDar", html_content)


async def send_annonce_notification_to_pro(
    to_email: str, 
    pro_name: str, 
    client_name: str,
    annonce_title: str,
    annonce_id: str,
    city: str,
    category: str
) -> dict:
    """Send notification to professional about a new announcement"""
    annonce_link = f"{FRONTEND_URL}/dashboard/annonces"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="background: linear-gradient(90deg, #7C3AED, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">MyDar</h1>
        </div>
        
        <div style="background-color: #dbeafe; border-left: 4px solid #3b82f6; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
            <strong style="color: #1e40af;">🔔 Nouvelle demande de service !</strong>
        </div>
        
        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; margin-bottom: 20px;">
            <h2 style="color: #1f2937; margin-top: 0;">Bonjour {pro_name} !</h2>
            <p>Un client recherche un professionnel pour une intervention dans votre secteur :</p>
            
            <div style="background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="color: #7C3AED; margin-top: 0;">{annonce_title}</h3>
                <p><strong>📍 Ville :</strong> {city}</p>
                <p><strong>🏷️ Catégorie :</strong> {category}</p>
                <p><strong>👤 Client :</strong> {client_name}</p>
            </div>
            
            <p>Vous avez été sélectionné par ce client parmi les professionnels de confiance. Répondez rapidement pour augmenter vos chances d'obtenir cette mission !</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{annonce_link}" style="display: inline-block; background: linear-gradient(90deg, #7C3AED, #06B6D4); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">Voir et répondre à l'annonce</a>
            </div>
        </div>
        
        <div style="text-align: center; color: #6b7280; font-size: 12px;">
            <p style="margin-top: 20px;">© 2025 MyDar - Smart Home</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(to_email, f"🔔 Nouvelle demande : {annonce_title} - MyDar", html_content)


async def send_response_notification_to_client(
    to_email: str,
    client_name: str,
    pro_name: str,
    annonce_title: str,
    annonce_id: str,
    message_preview: str
) -> dict:
    """Send notification to client when a professional responds"""
    annonce_link = f"{FRONTEND_URL}/dashboard/my-annonces/{annonce_id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="background: linear-gradient(90deg, #7C3AED, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">MyDar</h1>
        </div>
        
        <div style="background-color: #d1fae5; border-left: 4px solid #10b981; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
            <strong style="color: #065f46;">✅ Un professionnel a répondu à votre annonce !</strong>
        </div>
        
        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; margin-bottom: 20px;">
            <h2 style="color: #1f2937; margin-top: 0;">Bonjour {client_name} !</h2>
            <p>Bonne nouvelle ! <strong>{pro_name}</strong> a répondu à votre annonce :</p>
            
            <div style="background-color: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="color: #7C3AED; margin-top: 0;">{annonce_title}</h3>
                <p style="color: #6b7280; font-style: italic;">"{message_preview[:150]}..."</p>
            </div>
            
            <p>Consultez les détails de cette réponse et le profil du professionnel pour faire votre choix.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{annonce_link}" style="display: inline-block; background: linear-gradient(90deg, #7C3AED, #06B6D4); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">Voir la réponse</a>
            </div>
        </div>
        
        <div style="text-align: center; color: #6b7280; font-size: 12px;">
            <p style="margin-top: 20px;">© 2025 MyDar - Smart Home</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(to_email, f"✅ Réponse à votre annonce : {annonce_title} - MyDar", html_content)


async def send_admin_purchase_notification(purchase_request: dict, user: dict) -> dict:
    """Send notification email to admin about new purchase request"""
    # Get admin email - try to find admin user or use default
    admin_email = os.environ.get("ADMIN_EMAIL", "sassi.med92@gmail.com")
    
    # Build items HTML
    items_html = ""
    for item in purchase_request["items"]:
        price_str = f"{item['product_price']:.2f} €" if item.get('product_price') else "Sur demande"
        items_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{item['product_name']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">{item['quantity']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">{price_str}</td>
        </tr>
        """
    
    total_str = f"{purchase_request['total_estimated']:.2f} €" if purchase_request.get('total_estimated') else "À calculer"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="background: linear-gradient(90deg, #7C3AED, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">MyDar</h1>
        </div>
        
        <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
            <strong style="color: #92400e;">🛒 Nouvelle demande d'achat !</strong>
        </div>
        
        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; margin-bottom: 20px;">
            <h2 style="color: #1f2937; margin-top: 0;">Informations client</h2>
            <p><strong>Nom :</strong> {purchase_request['user_name']}</p>
            <p><strong>Email :</strong> {purchase_request['user_email']}</p>
            <p><strong>Téléphone :</strong> {purchase_request.get('user_phone') or 'Non renseigné'}</p>
            <p><strong>Date :</strong> {purchase_request['created_at'].strftime('%d/%m/%Y à %H:%M')}</p>
            
            <h3 style="color: #1f2937; margin-top: 25px;">Produits commandés</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #e5e7eb;">
                        <th style="padding: 10px; text-align: left;">Produit</th>
                        <th style="padding: 10px; text-align: center;">Qté</th>
                        <th style="padding: 10px; text-align: right;">Prix unit.</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            
            <div style="margin-top: 20px; text-align: right; font-size: 18px;">
                <strong>Total estimé : {total_str}</strong>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{FRONTEND_URL}/admin/purchase-requests" style="display: inline-block; background: linear-gradient(90deg, #8B5CF6, #06B6D4, #22C55E); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">Gérer la demande</a>
        </div>
        
        <div style="text-align: center; color: #6b7280; font-size: 12px;">
            <p style="margin-top: 20px;">© 2025 MyDar - Smart Home</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(admin_email, f"🛒 Nouvelle demande d'achat - {purchase_request['user_name']}", html_content)
