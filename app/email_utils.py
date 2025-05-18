from typing import List
from pydantic import EmailStr, BaseModel
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

SMTP_USERNAME = "cattykittian@gmail.com"
SMTP_PASSWORD = "xprktykmauwfvtvw"  # App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # Using TLS port
SMTP_SENDER_NAME = "PayZen"
SMTP_SENDER_EMAIL = "cattykittian@gmail.com"

async def send_email(email: str, subject: str, body: str) -> bool:
    """Send email using direct SMTP connection."""
    try:
        logger.info(f"Attempting to send email to {email}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((SMTP_SENDER_NAME, SMTP_SENDER_EMAIL))  # Properly format the From header
        msg['To'] = email
        
        # Attach HTML body
        msg.attach(MIMEText(body, 'html'))
        
        # Create SMTP connection
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            logger.info("Connected to SMTP server")
            server.starttls()
            logger.info("Started TLS")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            logger.info("Logged in successfully")
            
            # Send email
            server.send_message(msg)
            logger.info(f"Email sent successfully to {email}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def send_bill_reminder(email: str, bill_name: str, due_date: str, amount: float, days_left: int) -> bool:
    """Send a bill reminder email."""
    subject = f"🔔 Reminder: {bill_name} bill due in {days_left} days"
    
    # Color coding based on urgency
    urgency_color = "#ff4444" if days_left <= 2 else "#ff9900" if days_left <= 5 else "#00cc44"
    
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; border-bottom: 2px solid {urgency_color};">Bill Payment Reminder</h2>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p style="color: {urgency_color}; font-weight: bold; font-size: 18px;">
                Due in {days_left} {'day' if days_left == 1 else 'days'}!
            </p>
            <ul style="list-style: none; padding: 0;">
                <li style="margin: 10px 0;"><strong>Bill:</strong> {bill_name}</li>
                <li style="margin: 10px 0;"><strong>Amount:</strong> ${amount:.2f}</li>
                <li style="margin: 10px 0;"><strong>Due Date:</strong> {due_date}</li>
            </ul>
        </div>
        <p style="color: #666;">Please ensure timely payment to earn your reward points! 🎁</p>
        <div style="text-align: center; margin-top: 20px;">
            <a href="http://localhost:8000/login" 
               style="background-color: #007bff; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px;">
                Log in to PayZen
            </a>
        </div>
    </div>
    """
    
    return await send_email(email, subject, body)

async def send_bill_created_confirmation(email: str, bill_name: str, due_date: str, amount: float) -> bool:
    """Send a confirmation email when a new bill is created."""
    subject = f"✅ New Bill Added: {bill_name}"
    
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; border-bottom: 2px solid #00cc44;">New Bill Added Successfully</h2>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p style="color: #00cc44; font-weight: bold;">Bill Details:</p>
            <ul style="list-style: none; padding: 0;">
                <li style="margin: 10px 0;"><strong>Bill:</strong> {bill_name}</li>
                <li style="margin: 10px 0;"><strong>Amount:</strong> ${amount:.2f}</li>
                <li style="margin: 10px 0;"><strong>Due Date:</strong> {due_date}</li>
            </ul>
        </div>
        <p style="color: #666;">We'll send you reminders before the due date. 🔔</p>
        <div style="text-align: center; margin-top: 20px;">
            <a href="http://localhost:8000/dashboard" 
               style="background-color: #007bff; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px;">
                View Dashboard
            </a>
        </div>
    </div>
    """
    
    return await send_email(email, subject, body)

async def send_payment_confirmation(email: str, bill_name: str, amount: float, points_earned: int) -> bool:
    """Send a confirmation email when a bill is paid."""
    subject = f"✅ Payment Confirmed: {bill_name}"
    
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; border-bottom: 2px solid #00cc44;">Payment Successful!</h2>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p style="color: #00cc44; font-weight: bold;">Payment Details:</p>
            <ul style="list-style: none; padding: 0;">
                <li style="margin: 10px 0;"><strong>Bill:</strong> {bill_name}</li>
                <li style="margin: 10px 0;"><strong>Amount Paid:</strong> ${amount:.2f}</li>
                <li style="margin: 10px 0;"><strong>Points Earned:</strong> {points_earned} 🌟</li>
            </ul>
        </div>
        <p style="color: #666;">Thank you for your timely payment! You've earned {points_earned} reward points. 🎁</p>
        <div style="text-align: center; margin-top: 20px;">
            <a href="http://localhost:8000/rewards" 
               style="background-color: #007bff; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px;">
                View Your Rewards
            </a>
        </div>
        <p style="font-size: 12px; color: #999; margin-top: 20px; text-align: center;">
            This is a payment confirmation from PayZen. Please keep this for your records.
        </p>
    </div>
    """
    
    return await send_email(email, subject, body)

async def send_reward_claimed_confirmation(email: str, reward_name: str, points_used: int, points_remaining: int) -> bool:
    """Send a confirmation email when a reward is claimed."""
    subject = f"🎁 Reward Claimed: {reward_name}"
    
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; border-bottom: 2px solid #ff9900;">Reward Claimed Successfully!</h2>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p style="color: #ff9900; font-weight: bold;">Reward Details:</p>
            <ul style="list-style: none; padding: 0;">
                <li style="margin: 10px 0;"><strong>Reward:</strong> {reward_name}</li>
                <li style="margin: 10px 0;"><strong>Points Used:</strong> {points_used}</li>
                <li style="margin: 10px 0;"><strong>Points Remaining:</strong> {points_remaining}</li>
            </ul>
        </div>
        <p style="color: #666;">Congratulations on claiming your reward! 🎉</p>
        <div style="text-align: center; margin-top: 20px;">
            <a href="http://localhost:8000/dashboard" 
               style="background-color: #007bff; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px;">
                Back to Dashboard
            </a>
        </div>
        <p style="font-size: 12px; color: #999; margin-top: 20px; text-align: center;">
            This is a reward claim confirmation from PayZen.
        </p>
    </div>
    """
    
    return await send_email(email, subject, body)

async def send_low_points_notification(email: str, current_points: int) -> bool:
    """Send a notification when user's points are low."""
    subject = "💡 Earn More Reward Points!"
    
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; border-bottom: 2px solid #ff9900;">Your Reward Points Update</h2>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <p style="color: #ff9900; font-weight: bold;">Current Points Balance: {current_points}</p>
            <p>Want to earn more points? Here's how:</p>
            <ul style="list-style: none; padding: 0;">
                <li style="margin: 10px 0;">✅ Pay your bills on time</li>
                <li style="margin: 10px 0;">✅ Set up automatic payments</li>
                <li style="margin: 10px 0;">✅ Complete your profile</li>
            </ul>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <a href="http://localhost:8000/bills" 
               style="background-color: #007bff; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px;">
                View Your Bills
            </a>
        </div>
        <p style="font-size: 12px; color: #999; margin-top: 20px; text-align: center;">
            Keep earning points with PayZen!
        </p>
    </div>
    """
    
    return await send_email(email, subject, body) 