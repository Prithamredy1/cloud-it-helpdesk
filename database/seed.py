from app import db
from app.models.user import User
from app.models.ticket import Category, SLAPolicy, KnowledgeArticle, Ticket, WorkLog, Comment
from datetime import datetime, timedelta

def seed_data():
    if User.query.first():
        return  # already seeded

    # Users
    admin = User(full_name='Admin User', email='admin@company.com', role='admin', department='IT')
    admin.set_password('Admin@123')
    
    tech1 = User(full_name='Rajesh Kumar', email='technician@company.com', role='technician', department='IT Support')
    tech1.set_password('Tech@123')
    
    tech2 = User(full_name='Priya Sharma', email='priya.tech@company.com', role='technician', department='IT Support')
    tech2.set_password('Tech@123')
    
    emp1 = User(full_name='Amit Patel', email='employee@company.com', role='employee', department='Finance')
    emp1.set_password('Emp@123')
    
    emp2 = User(full_name='Sneha Reddy', email='sneha@company.com', role='employee', department='HR')
    emp2.set_password('Emp@123')
    
    emp3 = User(full_name='Vikram Singh', email='vikram@company.com', role='employee', department='Sales')
    emp3.set_password('Emp@123')
    
    db.session.add_all([admin, tech1, tech2, emp1, emp2, emp3])
    db.session.commit()

    # Categories
    cats = [
        Category(category_name='Hardware', description='Laptop, desktop, peripherals'),
        Category(category_name='Software', description='Applications, OS, updates'),
        Category(category_name='Network', description='Internet, Wi-Fi, VPN, DNS'),
        Category(category_name='Account & Access', description='Passwords, permissions, accounts'),
        Category(category_name='Email', description='Outlook, email delivery'),
        Category(category_name='Printer & Peripherals', description='Printers, scanners'),
    ]
    db.session.add_all(cats)
    db.session.commit()

    # SLA Policies
    slas = [
        SLAPolicy(priority='Critical', response_target_minutes=15, resolution_target_minutes=240),
        SLAPolicy(priority='High', response_target_minutes=30, resolution_target_minutes=480),
        SLAPolicy(priority='Medium', response_target_minutes=240, resolution_target_minutes=1440),
        SLAPolicy(priority='Low', response_target_minutes=480, resolution_target_minutes=2880),
    ]
    db.session.add_all(slas)
    db.session.commit()

    # Knowledge Articles
    articles = [
        KnowledgeArticle(
            title='Troubleshoot Internet Connectivity Issues',
            category_id=3,
            problem_description='User cannot access websites despite Wi-Fi connection.',
            symptoms='Wi-Fi connected, no internet access, pages fail to load.',
            diagnostic_steps='1. ipconfig /all\n2. ping 192.168.1.1 (gateway)\n3. ping 8.8.8.8\n4. nslookup google.com',
            resolution_steps='Correct DNS settings or renew IP with ipconfig /renew. Check proxy settings.',
            verification_steps='Browse to google.com and confirm access.',
            created_by=tech1.id
        ),
        KnowledgeArticle(
            title='Resolve High CPU Utilization on Windows',
            category_id=2,
            problem_description='Laptop running very slowly, high CPU usage.',
            symptoms='System lag, Task Manager shows >80% CPU.',
            diagnostic_steps='1. Open Task Manager\n2. Sort by CPU\n3. Identify top processes\n4. Check Startup apps\n5. Review Event Viewer',
            resolution_steps='End unnecessary processes, disable startup items, scan for malware, update drivers.',
            verification_steps='Confirm CPU usage drops below 30% idle.',
            created_by=tech1.id
        ),
        KnowledgeArticle(
            title='Fix Outlook Not Receiving Emails',
            category_id=5,
            problem_description='Outlook opens but new emails do not appear.',
            symptoms='Inbox empty of new mail, send works sometimes.',
            diagnostic_steps='1. Check account settings\n2. Test online OWA\n3. Review send/receive logs\n4. Check mailbox quota',
            resolution_steps='Repair Outlook profile, clear cache, recreate account if needed.',
            verification_steps='Send test email and confirm receipt.',
            created_by=tech2.id
        ),
        KnowledgeArticle(
            title='Troubleshoot VPN Connection Failures',
            category_id=3,
            problem_description='Unable to connect to company VPN.',
            symptoms='Connection timeout, authentication failure, or disconnects.',
            diagnostic_steps='1. Verify credentials\n2. Check internet connectivity\n3. Review VPN client logs\n4. Test different network',
            resolution_steps='Update VPN client, reset credentials, check firewall, contact network team.',
            verification_steps='Successfully connect and access internal resources.',
            created_by=tech1.id
        ),
        KnowledgeArticle(
            title='Windows Account Locked Out',
            category_id=4,
            problem_description='User cannot log in - account locked.',
            symptoms='Login fails with lock message.',
            diagnostic_steps='1. Confirm lock status in AD or local\n2. Check failed login attempts\n3. Verify policy',
            resolution_steps='Unlock account via admin tools, reset password if required, educate on policy.',
            verification_steps='User successfully logs in.',
            created_by=admin.id
        ),
    ]
    db.session.add_all(articles)
    db.session.commit()

    # Sample Tickets
    now = datetime.utcnow()
    
    t1 = Ticket(
        ticket_number='INC-1001',
        request_type='Incident',
        subject='Cannot access websites - Wi-Fi connected but no internet',
        description='My laptop shows Wi-Fi connected with full bars, but I cannot open any website. I have an important financial report to submit by EOD. Location: Finance Department, 3rd floor.',
        category_id=3,
        created_by=emp1.id,
        assigned_to=tech1.id,
        priority='High',
        status='In Progress',
        affected_device='Dell Latitude 5420',
        location='Finance Dept',
        impact='High',
        urgency='High',
        created_at=now - timedelta(hours=2),
        first_response_at=now - timedelta(hours=1, minutes=40)
    )
    
    t2 = Ticket(
        ticket_number='INC-1002',
        request_type='Incident',
        subject='Outlook not receiving new emails',
        description='Outlook opens fine, I can send emails, but no new emails are arriving in my inbox since yesterday morning.',
        category_id=5,
        created_by=emp2.id,
        assigned_to=tech2.id,
        priority='Medium',
        status='Assigned',
        affected_device='HP EliteBook',
        location='HR Dept',
        impact='Medium',
        urgency='Medium',
        created_at=now - timedelta(hours=5)
    )
    
    t3 = Ticket(
        ticket_number='SR-1001',
        request_type='Service Request',
        subject='Request for Adobe Acrobat installation',
        description='Need Adobe Acrobat Pro installed for reviewing contracts. Manager approval attached in notes.',
        category_id=2,
        created_by=emp3.id,
        priority='Low',
        status='Open',
        affected_device='Lenovo ThinkPad',
        location='Sales Dept',
        impact='Low',
        urgency='Low',
        created_at=now - timedelta(hours=1)
    )
    
    t4 = Ticket(
        ticket_number='INC-1003',
        request_type='Incident',
        subject='Laptop running extremely slow',
        description='System takes 5+ minutes to boot and applications freeze frequently. Started after Windows update last week.',
        category_id=2,
        created_by=emp1.id,
        assigned_to=tech1.id,
        priority='Medium',
        status='Resolved',
        affected_device='Dell Latitude 5420',
        location='Finance Dept',
        impact='Medium',
        urgency='Medium',
        created_at=now - timedelta(days=2),
        first_response_at=now - timedelta(days=1, hours=20),
        resolved_at=now - timedelta(hours=12),
        resolution_notes='Identified high CPU from background update service and too many startup apps. Disabled unnecessary startups, cleaned temp files, verified performance improved.'
    )
    
    t5 = Ticket(
        ticket_number='INC-1004',
        request_type='Incident',
        subject='Printer offline - Finance floor shared printer',
        description='HP LaserJet on 3rd floor shows offline. Multiple users affected.',
        category_id=6,
        created_by=emp2.id,
        assigned_to=tech2.id,
        priority='High',
        status='Pending User',
        affected_device='HP LaserJet Pro M404',
        location='Finance Dept',
        impact='High',
        urgency='Medium',
        created_at=now - timedelta(hours=8),
        first_response_at=now - timedelta(hours=7)
    )
    
    db.session.add_all([t1, t2, t3, t4, t5])
    db.session.commit()

    # Work logs for t1
    wl1 = WorkLog(ticket_id=t1.id, technician_id=tech1.id, 
                  activity_description='Initial triage: Confirmed Wi-Fi connected. Ran ipconfig /all - observed DNS servers pointing to incorrect addresses (10.0.0.1 instead of corporate DNS).',
                  time_spent_minutes=15, created_at=now - timedelta(hours=1, minutes=40))
    wl2 = WorkLog(ticket_id=t1.id, technician_id=tech1.id,
                  activity_description='Connectivity tests: ping gateway (192.168.1.1) successful. ping 8.8.8.8 successful. nslookup google.com failed with timeout. Root cause: DNS misconfiguration.',
                  time_spent_minutes=20, created_at=now - timedelta(hours=1, minutes=10))
    wl3 = WorkLog(ticket_id=t1.id, technician_id=tech1.id,
                  activity_description='Resolution: Updated DNS to corporate servers via network adapter properties. Verified nslookup and browser access. Advised user to test and confirm.',
                  time_spent_minutes=10, created_at=now - timedelta(minutes=30))
    
    # Work logs for t4
    wl4 = WorkLog(ticket_id=t4.id, technician_id=tech1.id,
                  activity_description='Investigated slow performance. Task Manager: CPU 85% from Windows Update and Chrome processes. Disk 90%. Disabled 8 startup items, cleared 12GB temp files, ran disk cleanup.',
                  time_spent_minutes=45, created_at=now - timedelta(hours=18))
    
    db.session.add_all([wl1, wl2, wl3, wl4])
    
    # Comments
    c1 = Comment(ticket_id=t1.id, user_id=tech1.id, comment='Hi Amit, I have identified a DNS configuration issue. Working on the fix now.', created_at=now - timedelta(hours=1, minutes=35))
    c2 = Comment(ticket_id=t1.id, user_id=emp1.id, comment='Thank you. Please prioritize as I have a deadline.', created_at=now - timedelta(hours=1, minutes=30))
    c3 = Comment(ticket_id=t5.id, user_id=tech2.id, comment='Checked printer. It appears offline due to network. Can you confirm if the power light is on and cable is connected?', created_at=now - timedelta(hours=6))
    
    db.session.add_all([c1, c2, c3])
    db.session.commit()
    print('Database seeded successfully.')
