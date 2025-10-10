// frontend/src/App.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';

const API_URL = '/api';

// --- STYLES COMPONENT (Integrated, with NEW styles for progress bars) ---
const GlobalStyles = () => (
    <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        :root {
            --primary-color: #2a6fdb; --primary-hover: #1e5a9b; --secondary-color: #6c757d;
            --background-color: #f8f9fa; --surface-color: #ffffff; --text-color: #212529;
            --border-color: #dee2e6; --danger-color: #dc3545; --danger-hover: #a71d2a;
            --success-color: #198754; --warning-color: #ffc107; --font-family: 'Inter', sans-serif;
        }
        body { font-family: var(--font-family); background-color: var(--background-color); color: var(--text-color); margin: 0; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .app-header { display: flex; justify-content: space-between; align-items: center; background-color: var(--surface-color); padding: 1.5rem 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); margin-bottom: 2rem; }
        .app-header h1 { font-size: 2rem; font-weight: 700; color: var(--primary-color); margin: 0; }
        .btn { padding: 0.75rem 1.5rem; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.2s ease-in-out; text-align: center; }
        .btn:disabled { background-color: var(--secondary-color); cursor: not-allowed; opacity: 0.7; }
        .btn-primary { background-color: var(--primary-color); color: white; }
        .btn-primary:hover:not(:disabled) { background-color: var(--primary-hover); transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .btn-danger { background-color: var(--danger-color); color: white; }
        .btn-danger:hover:not(:disabled) { background-color: var(--danger-hover); }
        .form-container { background-color: var(--surface-color); padding: 2.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); max-width: 500px; margin: 2rem auto; }
        .form-container h2 { text-align: center; margin-bottom: 2rem; font-size: 1.75rem; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--secondary-color); }
        .form-input { width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 8px; font-size: 1rem; box-sizing: border-box; }
        .form-input:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(42, 111, 219, 0.2); }
        .form-checkbox { width: 1.25rem; height: 1.25rem; cursor: pointer; }
        .password-container { position: relative; display: flex; align-items: center; }
        .password-container .form-input { padding-right: 40px; }
        .password-toggle-btn { position: absolute; right: 10px; background: none; border: none; cursor: pointer; color: var(--secondary-color); padding: 0; display: flex; align-items: center; justify-content: center; }
        .error-message { background-color: rgba(220, 53, 69, 0.1); color: var(--danger-color); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; text-align: center; }
        .success-message { background-color: rgba(25, 135, 84, 0.1); color: var(--success-color); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; text-align: center; }
        .info-message { background-color: #eef2f7; color: #334d6e; padding: 1rem; border-radius: 8px; }
        .dashboard-layout { display: grid; grid-template-columns: 250px 1fr; gap: 2rem; }
        .dashboard-nav { background-color: var(--surface-color); padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); align-self: start; }
        .dashboard-nav h3 { margin-top: 0; font-size: 1.25rem; }
        .nav-menu { display: flex; flex-direction: column; gap: 0.5rem; }
        .nav-button { text-align: left; padding: 0.75rem 1rem; border: none; background-color: transparent; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 500; width: 100%; transition: background-color 0.2s, color 0.2s; }
        .nav-button:hover { background-color: #f1f3f5; }
        .nav-button.active { background-color: var(--primary-color); color: white; }
        .dashboard-content { background-color: var(--surface-color); padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .dashboard-content h2 { margin-top: 0; margin-bottom: 2rem; font-size: 1.75rem; }
        .table-container { overflow-x: auto; border: 1px solid var(--border-color); border-radius: 12px; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 1rem; text-align: left; border-bottom: 1px solid var(--border-color); white-space: normal; }
        .table thead th { background-color: #f8f9fa; font-weight: 600; }
        .table tbody tr:last-child td { border-bottom: none; }
        .table tbody tr:hover { background-color: #f1f3f5; }
        .filter-bar { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }
        .capitalize { text-transform: capitalize; }
        .text-center { text-align: center; }
        .mt-1 { margin-top: 1rem; }
        .mt-2 { margin-top: 2rem; }
        .mb-1 { margin-bottom: 1rem; }
        .mb-2 { margin-bottom: 2rem; }
        .results-container { margin-top: 2rem; }
        .results-summary { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; }
        .results-list { list-style-type: none; padding: 0; max-height: 300px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 8px; }
        .results-list li { display: flex; align-items: center; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color); }
        .results-list li:last-child { border-bottom: none; }
        .result-icon { margin-right: 1rem; }
        .result-success .result-icon { color: var(--success-color); }
        .result-failure .result-icon { color: var(--danger-color); }
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background-color: var(--surface-color); padding: 2.5rem; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15); width: 90%; max-width: 450px; }
        .modal-header { margin-bottom: 1.5rem; }
        .modal-header h3 { margin: 0; font-size: 1.5rem; }
        .modal-body { margin-bottom: 2rem; font-size: 1rem; color: var(--secondary-color); }
        .modal-footer { display: flex; justify-content: flex-end; gap: 1rem; }
        .notification { position: fixed; top: 20px; right: 20px; padding: 1rem 1.5rem; border-radius: 8px; color: white; z-index: 1001; box-shadow: 0 4px 12px rgba(0,0,0,0.1); animation: fadeInOut 4s ease-in-out; }
        .notification.error { background-color: var(--danger-color); }
        @keyframes fadeInOut { 0% { opacity: 0; transform: translateY(-10px); } 10% { opacity: 1; transform: translateY(0); } 90% { opacity: 1; transform: translateY(0); } 100% { opacity: 0; transform: translateY(-10px); } }

        /* --- NEW STYLES FOR UPLOADER --- */
        .upload-list { list-style: none; padding: 0; margin-top: 1.5rem; }
        .upload-item { display: flex; align-items: center; gap: 1rem; padding: 1rem; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 1rem; }
        .upload-item-info { flex-grow: 1; }
        .upload-item-info p { margin: 0; font-weight: 500; }
        .upload-item-info small { color: var(--secondary-color); text-transform: capitalize; }
        .progress-bar-container { width: 100%; background-color: #e9ecef; border-radius: 8px; overflow: hidden; height: 10px; margin-top: 0.5rem; }
        .progress-bar { height: 100%; width: 0%; background-color: var(--primary-color); transition: width 0.3s ease-in-out; }
        .progress-bar.processing { animation: pulse 2s infinite; }
        .progress-bar.success { background-color: var(--success-color); }
        .progress-bar.failure { background-color: var(--danger-color); }
        .progress-bar.cancelled { background-color: var(--secondary-color); }
        @keyframes pulse { 0% { background-color: #a8c5f0; } 50% { background-color: var(--primary-color); } 100% { background-color: #a8c5f0; } }

    `}</style>
);

const columnTranslations = {
    first_name: 'Prénom', last_name: 'Nom de famille', birth_date: 'Date de Naissance',
    delivery_date: 'Date de Délivrance', expiration_date: "Date d'Expiration", nationality: 'Nationalité',
    passport_number: 'Numéro de Passeport', confidence_score: 'Score de Confiance', email: 'Email',
    phone_number: 'Numéro de Téléphone', user_name: "Nom d'Utilisateur", role: 'Rôle',
    destination: 'Destination', token: 'Jeton', expires_at: 'Expire Le', is_used: 'Utilisé', actions: 'Actions'
};

const EyeIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>);
const EyeOffIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>);
function PasswordInput({ value, onChange, name, placeholder, required = false }) {
    const [showPassword, setShowPassword] = useState(false);
    return (
        <div className="password-container">
            <input type={showPassword ? 'text' : 'password'} name={name} value={value} onChange={onChange} className="form-input" placeholder={placeholder} required={required} autoComplete="new-password" />
            <button type="button" className="password-toggle-btn" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Cacher le mot de passe' : 'Afficher le mot de passe'}>
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
            </button>
        </div>
    );
}

function Modal({ isOpen, onClose, onConfirm, title, children }) {
    if (!isOpen) return null;
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header"><h3>{title}</h3></div>
                <div className="modal-body">{children}</div>
                <div className="modal-footer">
                    <button onClick={onClose} className="btn" style={{ backgroundColor: 'var(--secondary-color)', color: 'white' }}>Annuler</button>
                    <button onClick={onConfirm} className="btn btn-danger">Confirmer</button>
                </div>
            </div>
        </div>
    );
}

function Notification({ message, type, onClear }) {
    useEffect(() => {
        const timer = setTimeout(() => { onClear(); }, 4000);
        return () => clearTimeout(timer);
    }, [onClear]);

    if (!message) return null;
    return <div className={`notification ${type}`}>{message}</div>;
}

export default function App() {
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [user, setUser] = useState(null);
    const [view, setView] = useState('login');
    const logout = useCallback(() => { localStorage.removeItem('token'); setToken(null); setUser(null); window.history.pushState({}, '', '/'); setView('login'); }, []);
    const fetchUser = useCallback(async () => {
        const currentToken = localStorage.getItem('token');
        if (currentToken) {
            try {
                const response = await fetch(`${API_URL}/users/me`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
                if (response.ok) { const data = await response.json(); setUser(data); setView('dashboard'); } else { logout(); }
            } catch (error) { console.error("Échec de la récupération de l'utilisateur:", error); logout(); }
        } else {
            const path = window.location.pathname;
            if (path.startsWith('/register/')) { setView('register'); } else { setView('login'); }
        }
    }, [logout]);
    useEffect(() => {
        fetchUser();
        const handlePopState = () => fetchUser();
        window.addEventListener('popstate', handlePopState);
        return () => window.removeEventListener('popstate', handlePopState);
    }, [fetchUser]);
    const renderView = () => {
        const path = window.location.pathname;
        if (view === 'register' || path.startsWith('/register/')) { const registrationToken = path.split('/')[2]; return <RegistrationPage registrationToken={registrationToken} />; }
        switch (view) {
            case 'login': return <Login setToken={setToken} fetchUser={fetchUser} />;
            case 'dashboard': return <Dashboard user={user} logout={logout} token={token} fetchUser={fetchUser} />;
            default: return <Login setToken={setToken} fetchUser={fetchUser} />;
        }
    };
    return (<><GlobalStyles /><div className="container"><header className="app-header"><h1>Gestionnaire de Voyages</h1>{user && <button onClick={logout} className="btn btn-danger">Déconnexion</button>}</header><main>{renderView()}</main></div></>);
}

function Login({ setToken, fetchUser }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        const formData = new URLSearchParams({ username, password });
        try {
            const response = await fetch(`${API_URL}/token`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: formData, });
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                setToken(data.access_token);
                fetchUser();
            } else {
                if (response.status === 429) {
                    setError("Trop de tentatives de connexion. Veuillez réessayer dans une minute.");
                } else {
                    const errorData = await response.json();
                    setError(errorData.detail || 'Échec de la connexion.');
                }
            }
        } catch (err) {
            setError('Une erreur est survenue. Veuillez réessayer.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="form-container">
            <h2>Connexion</h2>
            {error && <p className="error-message">{error}</p>}
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Nom d'utilisateur</label>
                    <input type="text" value={username} onChange={e => setUsername(e.target.value)} className="form-input" required />
                </div>
                <div className="form-group">
                    <label>Mot de passe</label>
                    <PasswordInput name="password" value={password} onChange={e => setPassword(e.target.value)} required={true} />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={isLoading}>
                    {isLoading ? 'Connexion en cours...' : 'Se connecter'}
                </button>
            </form>
        </div>
    );
}

function RegistrationPage({ registrationToken }) {
    const [formData, setFormData] = useState({ first_name: '', last_name: '', email: '', phone_number: '', user_name: '', password: '' });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    useEffect(() => {
        const fetchInvitation = async () => {
            if (!registrationToken) { setError("Aucun jeton d'inscription fourni."); setIsLoading(false); return; }
            try {
                const response = await fetch(`${API_URL}/invitations/${registrationToken}`);
                if (response.ok) { const data = await response.json(); setFormData(prev => ({ ...prev, email: data.email })); } else { setError((await response.json()).detail || "Lien d'inscription invalide ou expiré."); }
            } catch (err) { setError("Une erreur est survenue lors de la validation du lien d'inscription."); } finally { setIsLoading(false); }
        };
        fetchInvitation();
    }, [registrationToken]);
    const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });
    const handleSubmit = async (e) => {
        e.preventDefault(); setError(''); setSuccess('');
        try {
            const response = await fetch(`${API_URL}/users/?token=${registrationToken}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
            if (response.ok) { setSuccess('Inscription réussie ! Vous allez être redirigé vers la page de connexion.'); setTimeout(() => { window.history.pushState({}, '', '/'); window.location.reload(); }, 2000); } else { setError((await response.json()).detail || "Échec de l'inscription."); }
        } catch (err) { setError("Une erreur est survenue lors de l'inscription."); }
    };
    if (isLoading) return <p className="info-message">Chargement...</p>;
    if (success) return <div className="form-container"><p className="success-message">{success}</p></div>
    return (<div className="form-container"><h2>Créer un nouveau compte</h2>{error && <p className="error-message">{error}</p>}<form onSubmit={handleSubmit}><div className="form-group"><label>Prénom</label><input type="text" name="first_name" value={formData.first_name} onChange={handleChange} className="form-input" required /></div><div className="form-group"><label>Nom de famille</label><input type="text" name="last_name" value={formData.last_name} onChange={handleChange} className="form-input" required /></div><div className="form-group"><label>Email</label><input type="email" name="email" value={formData.email} onChange={handleChange} className="form-input" required readOnly /></div><div className="form-group"><label>Numéro de téléphone</label><input type="text" name="phone_number" value={formData.phone_number} onChange={handleChange} className="form-input" required /></div><div className="form-group"><label>Nom d'utilisateur</label><input type="text" name="user_name" value={formData.user_name} onChange={handleChange} className="form-input" required /></div><div className="form-group"><label>Mot de passe</label><PasswordInput name="password" value={formData.password} onChange={handleChange} required={true} /></div><button type="submit" className="btn btn-primary" style={{ width: '100%' }}>S'inscrire</button></form></div>);
}

function Dashboard({ user, token, fetchUser }) {
    const [activeTab, setActiveTab] = useState('passports');
    const [filterableUsers, setFilterableUsers] = useState([]);
    const [userSpecificDestinations, setUserSpecificDestinations] = useState([]);

    const fetchAdminData = useCallback(async () => {
        if (user.role !== 'admin') return;
        try {
            const filterableUsersRes = await fetch(`${API_URL}/admin/filterable-users`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (filterableUsersRes.ok) setFilterableUsers(await filterableUsersRes.json());
        } catch (error) { console.error("Échec de la récupération des données admin:", error); }
    }, [user, token]);

    const fetchUserDestinations = useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/destinations/`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) setUserSpecificDestinations(await response.json());
        } catch (error) { console.error("Échec de la récupération des destinations de l'utilisateur:", error); }
    }, [token]);

    useEffect(() => { fetchAdminData(); fetchUserDestinations(); }, [fetchAdminData, fetchUserDestinations]);

    const renderTabContent = () => {
        const passportFilterConfig = user.role === 'admin'
            ? [{ name: 'user_filter', placeholder: 'Filtrer par Utilisateur', options: filterableUsers, getOptionValue: (o) => o.id, getOptionLabel: (o) => `${o.first_name} ${o.last_name} (${o.user_name})` }]
            : null;
        const voyageFilterConfig = user.role === 'admin'
            ? [{ name: 'user_filter', placeholder: 'Filtrer par Utilisateur', options: filterableUsers, getOptionValue: (o) => o.id, getOptionLabel: (o) => `${o.first_name} ${o.last_name} (${o.user_name})` }]
            : null;
        const passportFields = { first_name: 'text', last_name: 'text', birth_date: 'date', delivery_date: 'date', expiration_date: 'date', nationality: 'text', passport_number: 'text', destination: 'text', confidence_score: 'number' };

        switch (activeTab) {
            case 'account': return <AccountEditor user={user} token={token} fetchUser={fetchUser} />;
            case 'passports': return <CrudManager title="Gérer les Passeports" endpoint="passports" token={token} user={user} fields={passportFields} filterConfig={passportFilterConfig} />;
            case 'voyages': return <CrudManager title="Gérer les Voyages" endpoint="voyages" token={token} user={user} fields={{ destination: 'text' }} filterConfig={voyageFilterConfig} />;
            case 'tools_export': return <ToolsAndExportPanel token={token} user={user} adminUsers={filterableUsers} userDestinations={userSpecificDestinations} />;
            case 'users': return user.role === 'admin' ? <CrudManager title="Gérer les Utilisateurs" endpoint="admin/users" token={token} user={user} fields={{ first_name: 'text', last_name: 'text', email: 'email', phone_number: 'text', user_name: 'text', password: 'password', role: 'text' }} /> : null;
            case 'invitations': return user.role === 'admin' ? <CrudManager title="Gérer les Invitations" endpoint="admin/invitations" token={token} user={user} fields={{ email: 'email', token: 'text', expires_at: 'datetime-local', is_used: 'checkbox' }} /> : null;
            default: return null;
        }
    };
    return (
        <div className="dashboard-layout">
            <nav className="dashboard-nav">
                <h3>Bienvenue, {user.first_name}!</h3>
                <div className="nav-menu">
                    <button onClick={() => setActiveTab('account')} className={`nav-button ${activeTab === 'account' ? 'active' : ''}`}>Mon Compte</button>
                    <button onClick={() => setActiveTab('passports')} className={`nav-button ${activeTab === 'passports' ? 'active' : ''}`}>Passeports</button>
                    <button onClick={() => setActiveTab('voyages')} className={`nav-button ${activeTab === 'voyages' ? 'active' : ''}`}>Voyages</button>
                    <button onClick={() => setActiveTab('tools_export')} className={`nav-button ${activeTab === 'tools_export' ? 'active' : ''}`}>Outils & Exportation</button>
                    {user.role === 'admin' && (
                        <> <hr />
                            <button onClick={() => setActiveTab('users')} className={`nav-button ${activeTab === 'users' ? 'active' : ''}`}>Gérer les Utilisateurs</button>
                            <button onClick={() => setActiveTab('invitations')} className={`nav-button ${activeTab === 'invitations' ? 'active' : ''}`}>Gérer les Invitations</button>
                        </>
                    )}
                </div>
            </nav>
            <div className="dashboard-content">{renderTabContent()}</div>
        </div>
    );
}

function AccountEditor({ user, token, fetchUser }) {
    const [formData, setFormData] = useState({ first_name: '', last_name: '', email: '', phone_number: '', password: '' });
    const [message, setMessage] = useState('');
    useEffect(() => { if (user) setFormData({ first_name: user.first_name, last_name: user.last_name, email: user.email, phone_number: user.phone_number, password: '' }); }, [user]);
    const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });
    const handleSubmit = async (e) => {
        e.preventDefault(); setMessage(''); const payload = { ...formData }; if (!payload.password) delete payload.password;
        const response = await fetch(`${API_URL}/users/me`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify(payload) });
        if (response.ok) { setMessage('Compte mis à jour avec succès !'); fetchUser(); } else { setMessage('Échec de la mise à jour du compte.'); }
    };
    return (<div><h2>Modifier Mon Compte</h2>{message && <p className="success-message">{message}</p>}<form onSubmit={handleSubmit}><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}><div className="form-group"><label>Prénom</label><input type="text" name="first_name" value={formData.first_name} onChange={handleChange} className="form-input" /></div><div className="form-group"><label>Nom de famille</label><input type="text" name="last_name" value={formData.last_name} onChange={handleChange} className="form-input" /></div><div className="form-group"><label>Email</label><input type="email" name="email" value={formData.email} onChange={handleChange} className="form-input" /></div><div className="form-group"><label>Numéro de téléphone</label><input type="text" name="phone_number" value={formData.phone_number} onChange={handleChange} className="form-input" /></div></div><div className="form-group"><label>Nouveau mot de passe (optionnel)</label><PasswordInput name="password" value={formData.password} onChange={handleChange} placeholder="Laisser vide pour conserver le mot de passe actuel" /></div><button type="submit" className="btn btn-primary">Enregistrer les modifications</button></form></div>);
}

function OcrUploader({ token, onUploadSuccess }) {
    const [uploadTasks, setUploadTasks] = useState([]);
    const [destination, setDestination] = useState('');
    const [destinations, setDestinations] = useState([]);
    const pollingIntervals = useRef({});

    useEffect(() => {
        const fetchDestinations = async () => {
            try {
                const response = await fetch(`${API_URL}/destinations/`, { headers: { 'Authorization': `Bearer ${token}` } });
                if (response.ok) setDestinations(await response.json());
            } catch (error) { console.error("Failed to fetch destinations:", error); }
        };
        fetchDestinations();
    }, [token]);

    useEffect(() => {
        return () => {
            Object.values(pollingIntervals.current).forEach(clearInterval);
        };
    }, []);

    const handleFileChange = (e) => {
        const newFiles = Array.from(e.target.files).map(file => ({
            id: `${file.name}-${file.lastModified}`,
            file: file,
            status: 'WAITING', // 'WAITING', 'PENDING', 'PROGRESS', 'SUCCESS', 'FAILURE', 'CANCELLED'
            progress: { status: 'En attente de traitement...' },
            taskId: null,
            result: null
        }));
        setUploadTasks(prev => [...prev, ...newFiles]);
        e.target.value = null; // Reset file input
    };

    const pollTaskStatus = useCallback((taskId, fileId) => {
        pollingIntervals.current[taskId] = setInterval(async () => {
            try {
                const response = await fetch(`${API_URL}/tasks/${taskId}/status`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!response.ok) throw new Error('Network response was not ok.');
                
                const data = await response.json();

                setUploadTasks(prev => prev.map(task =>
                    task.id === fileId ? { ...task, status: data.status, progress: data.progress || task.progress, result: data.result } : task
                ));

                if (['SUCCESS', 'FAILURE', 'CANCELLED'].includes(data.status)) {
                    clearInterval(pollingIntervals.current[taskId]);
                    delete pollingIntervals.current[taskId];
                    onUploadSuccess(true); // Signal to refresh data in the main view
                }
            } catch (error) {
                console.error("Polling error:", error);
                clearInterval(pollingIntervals.current[taskId]);
                delete pollingIntervals.current[taskId];
                setUploadTasks(prev => prev.map(task =>
                    task.id === fileId ? { ...task, status: 'FAILURE', progress: { status: 'Erreur de suivi.' } } : task
                ));
            }
        }, 5000); // Poll every 5 seconds
    }, [token, onUploadSuccess]);

    const handleSubmit = async () => {
        const filesToUpload = uploadTasks.filter(task => task.status === 'WAITING');
        if (filesToUpload.length === 0) return;

        const formData = new FormData();
        filesToUpload.forEach(task => {
            formData.append('files', task.file);
        });
        if (destination) formData.append('destination', destination);
        
        // Mark files as pending immediately for better UX
        setUploadTasks(prev => prev.map(t => filesToUpload.find(f => f.id === t.id) ? { ...t, status: 'PENDING' } : t));

        try {
            const response = await fetch(`${API_URL}/passports/upload-and-extract/`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (response.status === 202) {
                const data = await response.json(); // Expects { tasks: [{ task_id, filename }] }
                data.tasks.forEach(createdTask => {
                    const matchingFile = filesToUpload.find(f => f.file.name === createdTask.filename);
                    if (matchingFile) {
                        setUploadTasks(prev => prev.map(t =>
                            t.id === matchingFile.id ? { ...t, taskId: createdTask.task_id, status: 'PROGRESS', progress: { status: 'En cours de traitement...' } } : t
                        ));
                        pollTaskStatus(createdTask.task_id, matchingFile.id);
                    }
                });
            } else {
                const errorData = await response.json();
                setUploadTasks(prev => prev.map(t =>
                    filesToUpload.find(f => f.id === t.id) ? { ...t, status: 'FAILURE', progress: { status: errorData.detail || 'Upload failed.' } } : t
                ));
            }
        } catch (err) {
            console.error("Upload error:", err);
            setUploadTasks(prev => prev.map(t =>
                filesToUpload.find(f => f.id === t.id) ? { ...t, status: 'FAILURE', progress: { status: 'Erreur réseau.' } } : t
            ));
        }
    };
    
    const handleCancel = async (taskToCancel) => {
        if (!taskToCancel.taskId) return; // Can't cancel if no task ID yet
        
        clearInterval(pollingIntervals.current[taskToCancel.taskId]);
        delete pollingIntervals.current[taskToCancel.taskId];
        
        try {
            await fetch(`${API_URL}/tasks/${taskToCancel.taskId}/cancel`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setUploadTasks(prev => prev.map(task =>
                task.id === taskToCancel.id ? { ...task, status: 'CANCELLED', progress: { status: 'Annulation demandée.'} } : task
            ));
        } catch (error) {
            console.error("Failed to send cancel request:", error);
        }
    };
    
    const handleRemoveTask = (idToRemove) => {
        setUploadTasks(prev => prev.filter(task => task.id !== idToRemove));
    };

    const handleFinishAndClear = () => {
        setUploadTasks([]);
        onUploadSuccess(false); // Close the uploader view
    };

    const isUploading = uploadTasks.some(t => ['PENDING', 'PROGRESS'].includes(t.status));
    const waitingCount = uploadTasks.filter(t => t.status === 'WAITING').length;
    
    const getProgressBarClass = (status) => {
        switch(status) {
            case 'SUCCESS': return 'success';
            case 'FAILURE': return 'failure';
            case 'CANCELLED': return 'cancelled';
            case 'PROGRESS':
            case 'PENDING': return 'processing';
            default: return '';
        }
    }

    return (
        <div className="form-container" style={{ maxWidth: 'none', margin: 0, padding: '2rem' }}>
            <h3>Ajouter des Passeports via Téléchargement</h3>
            <div className="form-group">
                <label>Destination (Optionnel)</label>
                <input type="text" value={destination} onChange={(e) => setDestination(e.target.value)} className="form-input" list="destination-datalist-ocr" placeholder="Appliquer à tous les passeports des fichiers" autoComplete="off" />
                <datalist id="destination-datalist-ocr">{destinations.map(dest => <option key={dest} value={dest} />)}</datalist>
            </div>
            <div className="form-group">
                <label>Documents PDF (plusieurs fichiers possibles)</label>
                <input type="file" onChange={handleFileChange} accept="application/pdf" className="form-input" multiple disabled={isUploading} />
            </div>

            <ul className="upload-list">
                {uploadTasks.map(task => (
                    <li key={task.id} className="upload-item">
                        <div className="upload-item-info">
                            <p>{task.file.name}</p>
                            <small>{task.progress?.status || task.status}</small>
                            <div className="progress-bar-container">
                                <div
                                    className={`progress-bar ${getProgressBarClass(task.status)}`}
                                    style={{ width: ['SUCCESS', 'FAILURE', 'CANCELLED'].includes(task.status) ? '100%' : (['PROGRESS', 'PENDING'].includes(task.status) ? '50%' : '0%') }}
                                ></div>
                            </div>
                            {task.status === 'SUCCESS' && task.result && (
                                <small style={{color: 'var(--success-color)'}}>
                                    Succès: {task.result.successful_pages}, Échecs: {task.result.failed_pages?.length || 0}
                                </small>
                            )}
                             {task.status === 'FAILURE' && (
                                <small style={{color: 'var(--danger-color)'}}>
                                    Échec: {task.result || 'Une erreur est survenue.'}
                                </small>
                            )}
                        </div>
                        {['PENDING', 'PROGRESS'].includes(task.status) && (
                            <button onClick={() => handleCancel(task)} className="btn btn-danger">Annuler</button>
                        )}
                        {['SUCCESS', 'FAILURE', 'CANCELLED', 'WAITING'].includes(task.status) && (
                            <button onClick={() => handleRemoveTask(task.id)} className="btn" style={{backgroundColor: 'transparent', color: 'var(--danger-color)'}}>✕</button>
                        )}
                    </li>
                ))}
            </ul>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem' }}>
                <button onClick={handleFinishAndClear} className="btn" style={{ backgroundColor: 'var(--secondary-color)', color: 'white' }}>
                    Terminé
                </button>
                <button onClick={handleSubmit} className="btn btn-primary" disabled={isUploading || waitingCount === 0}>
                    {isUploading ? 'Traitement en cours...' : `Lancer le traitement (${waitingCount})`}
                </button>
            </div>
        </div>
    );
}

function CrudManager({ title, endpoint, token, user, fields, filterConfig }) {
    const [items, setItems] = useState([]);
    const [editingItem, setEditingItem] = useState(null);
    const [isCreating, setIsCreating] = useState(false);
    const [filters, setFilters] = useState({});
    const [showOcrUploader, setShowOcrUploader] = useState(false);
    const [dynamicDestinations, setDynamicDestinations] = useState([]);
    const [selectedItems, setSelectedItems] = useState([]);
    const selectAllCheckboxRef = useRef(null);

    const [modalState, setModalState] = useState({ isOpen: false, title: '', message: '', onConfirm: () => { } });
    const [notification, setNotification] = useState({ message: '', type: '' });

    const showNotification = (message, type = 'error') => {
        setNotification({ message, type });
    };

    const fetchDestinationsForUser = useCallback(async (userId) => {
        const query = userId ? `?user_id=${userId}` : '';
        try {
            const response = await fetch(`${API_URL}/destinations/${query}`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) setDynamicDestinations(await response.json());
        } catch (error) { console.error("Échec de la récupération des destinations:", error); }
    }, [token]);

    useEffect(() => { if (user.role === 'admin' && endpoint === 'passports') fetchDestinationsForUser(null); }, [user, endpoint, fetchDestinationsForUser]);

    const handleFilterChange = (filterName, value) => {
        const newFilters = { ...filters, [filterName]: value };
        if (user.role === 'admin' && filterName === 'user_filter') {
            fetchDestinationsForUser(value || null);
            newFilters.voyage_filter = '';
        }
        setFilters(newFilters);
    };

    const fetchData = useCallback(async () => {
        const activeFilters = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
        const query = new URLSearchParams(activeFilters);
        const url = `${API_URL}/${endpoint}/?${query.toString()}`;
        try {
            const response = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) setItems(await response.json());
            else console.error("Échec de la récupération des données pour", endpoint);
        } catch (error) { console.error("Erreur lors de la récupération des données:", error); }
    }, [endpoint, token, filters]);

    useEffect(() => { fetchData(); }, [fetchData]);

    useEffect(() => {
        if (selectAllCheckboxRef.current) {
            const allVisibleSelected = items.length > 0 && selectedItems.length === items.length;
            const someVisibleSelected = selectedItems.length > 0 && selectedItems.length < items.length;
            selectAllCheckboxRef.current.checked = allVisibleSelected;
            selectAllCheckboxRef.current.indeterminate = someVisibleSelected;
        }
    }, [selectedItems, items]);

    const handleSelect = (id) => setSelectedItems(prev => prev.includes(id) ? prev.filter(itemId => itemId !== id) : [...prev, id]);
    const handleSelectAll = (e) => setSelectedItems(e.target.checked ? items.map(item => item.id) : []);

    const confirmMultipleDelete = () => {
        if (selectedItems.length === 0) return;
        setModalState({
            isOpen: true,
            title: 'Confirmer la Suppression',
            message: `Êtes-vous sûr de vouloir supprimer les ${selectedItems.length} passeports sélectionnés ? Cette action est irréversible.`,
            onConfirm: () => handleMultipleDelete()
        });
    };

    const handleMultipleDelete = async () => {
        try {
            const response = await fetch(`${API_URL}/${endpoint}/delete-multiple`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ ids: selectedItems }),
            });
            if (response.ok || response.status === 204) {
                setSelectedItems([]);
                fetchData();
            } else {
                const errorData = await response.json();
                showNotification(`Échec de la suppression : ${errorData.detail || 'Erreur du serveur'}`);
            }
        } catch (error) {
            console.error("Erreur lors de la suppression multiple :", error);
            showNotification("Une erreur de réseau est survenue lors de la suppression.");
        } finally {
            setModalState({ isOpen: false, title: '', message: '', onConfirm: () => { } });
        }
    };

    const handleSave = (fromOcr = false) => {
        if (!fromOcr) {
            setEditingItem(null);
            setIsCreating(false);
            setShowOcrUploader(false);
        }
        fetchData();
    };

    const startCreating = () => {
        let newItem = Object.keys(fields).reduce((acc, key) => ({ ...acc, [key]: '' }), {});
        if (endpoint === 'admin/users') newItem.role = 'user';
        if (endpoint === 'admin/invitations') newItem = { email: '' };
        setEditingItem(newItem);
        setIsCreating(true);
    };

    if (showOcrUploader) return <OcrUploader token={token} onUploadSuccess={handleSave} />
    if (editingItem) return <CrudForm item={editingItem} isCreating={isCreating} onSave={handleSave} onCancel={() => setEditingItem(null)} fields={fields} endpoint={endpoint} token={token} />;
    const displayFields = { ...fields };
    if (endpoint === 'admin/users') delete displayFields.password;
    if (endpoint === 'admin/invitations' && isCreating) delete displayFields.token;
    if (endpoint === 'passports') delete displayFields.destination;

    return (
        <div>
            <Notification message={notification.message} type={notification.type} onClear={() => setNotification({ message: '', type: '' })} />
            <Modal isOpen={modalState.isOpen} onClose={() => setModalState({ ...modalState, isOpen: false })} onConfirm={modalState.onConfirm} title={modalState.title}>
                <p>{modalState.message}</p>
            </Modal>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} className="mb-2">
                <h2>{title}</h2>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    {endpoint === 'passports' && (
                        <button onClick={confirmMultipleDelete} className="btn btn-danger" disabled={selectedItems.length === 0}>
                            Supprimer ({selectedItems.length})
                        </button>
                    )}
                    {endpoint === 'passports' && (
                        <button onClick={() => setShowOcrUploader(true)} className="btn btn-primary" style={{ backgroundColor: 'var(--success-color)' }}>+ Ajouter par Téléchargement</button>
                    )}
                    <button onClick={startCreating} className="btn btn-primary">{endpoint === 'passports' ? '+ Ajouter Manuellement' : '+ Ajouter'}</button>
                </div>
            </div>

            {endpoint.includes('users') && !filterConfig && (<div className="filter-bar mb-2"><div className="form-group" style={{ flex: 1, marginBottom: 0 }}><input type="text" name="name_filter" placeholder="Filtrer par Nom, Nom d'utilisateur ou Email" onChange={(e) => handleFilterChange(e.target.name, e.target.value)} className="form-input" autoComplete="off"/></div></div>)}
            {filterConfig && (
                <div className="filter-bar mb-2">
                    {filterConfig.map(filter => (<ComboBoxFilter key={filter.name} {...filter} onChange={handleFilterChange} />))}
                    {user.role === 'admin' && endpoint === 'passports' && (<ComboBoxFilter key="voyage_filter" name="voyage_filter" placeholder="Filtrer par Destination" options={dynamicDestinations.map(d => ({ destination: d }))} getOptionValue={(o) => o.destination} getOptionLabel={(o) => o.destination} onChange={handleFilterChange} />)}
                </div>
            )}

            <div className="table-container">
                <table className="table">
                    <thead>
                        <tr>
                            {endpoint === 'passports' && (<th style={{ width: '1%' }}><input type="checkbox" ref={selectAllCheckboxRef} className="form-checkbox" onChange={handleSelectAll} disabled={items.length === 0}/></th>)}
                            {Object.keys(displayFields).map(field => (<th key={field}>{columnTranslations[field] || field.replace(/_/g, ' ')}</th>))}
                            <th>{columnTranslations['actions']}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.map(item => (
                            <tr key={item.id} style={{ backgroundColor: selectedItems.includes(item.id) ? '#eef2f7' : 'transparent' }}>
                                {endpoint === 'passports' && (<td><input type="checkbox" className="form-checkbox" checked={selectedItems.includes(item.id)} onChange={() => handleSelect(item.id)}/></td>)}
                                {Object.keys(displayFields).map(field => {
                                    let cellValue = item[field];
                                    if (field === 'confidence_score' && typeof cellValue === 'number') { cellValue = `${(cellValue * 100).toFixed(2)}%`; }
                                    return <td key={field}>{String(cellValue)}</td>
                                })}
                                <td>
                                    <button onClick={() => setEditingItem(item)} className="btn" style={{ backgroundColor: 'var(--warning-color)', color: 'black', marginRight: '0.5rem' }}>Modifier</button>
                                    {endpoint !== 'passports' && <button onClick={() => {/* Implement single delete with modal if needed */}} className="btn btn-danger">Supprimer</button>}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function CrudForm({ item, isCreating, onSave, onCancel, fields, endpoint, token }) {
    const [formData, setFormData] = useState(item);
    const [destinations, setDestinations] = useState([]);
    const [error, setError] = useState('');
    useEffect(() => {
        const initialData = { ...item };
        Object.entries(fields).forEach(([key, type]) => { if (type === 'datetime-local' && initialData[key]) { initialData[key] = new Date(initialData[key]).toISOString().slice(0, 16); } });
        if (endpoint === 'passports' && !isCreating && item.voyages && item.voyages.length > 0) { initialData.destination = item.voyages[0].destination; }
        setFormData(initialData);
    }, [item, fields, endpoint, isCreating]);
    
    useEffect(() => {
        if (endpoint === 'passports') {
            const fetchDestinations = async () => {
                try {
                    const response = await fetch(`${API_URL}/destinations/`, { headers: { 'Authorization': `Bearer ${token}` } });
                    if (response.ok) setDestinations(await response.json());
                } catch (error) { console.error("Échec de la récupération des destinations:", error); }
            };
            fetchDestinations();
        }
    }, [endpoint, token]);

    const handleChange = (e) => { const { name, value, type, checked } = e.target; setFormData({ ...formData, [name]: type === 'checkbox' ? checked : value }); };
    const handleSubmit = async (e) => {
        e.preventDefault(); setError('');
        let url = isCreating ? `${API_URL}/${endpoint}/` : `${API_URL}/${endpoint}/${item.id}`;
        let method = isCreating ? 'POST' : 'PUT';
        let body = { ...formData };
        if (body.confidence_score === '') { body.confidence_score = null; }
        if (endpoint === 'admin/invitations' && isCreating) body = { email: formData.email };
        if (endpoint === 'admin/users' && !isCreating && !body.password) delete body.password;
        const response = await fetch(url, { method, headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify(body), });
        if (response.ok) { onSave(); } else { const errorData = await response.json(); setError(errorData.detail || "Échec de l'enregistrement de l'élément."); }
    };
    const formFields = { ...fields };
    if (formFields.confidence_score) { delete formFields.confidence_score; }
    if (isCreating && endpoint === 'admin/invitations') { return (<form onSubmit={handleSubmit} className="form-container" style={{ maxWidth: 'none', margin: 0, padding: '2rem' }}><h3>Créer une nouvelle invitation</h3>{error && <p className="error-message">{error}</p>}<div className="form-group"><label>Email</label><input type="email" name="email" value={formData.email || ''} onChange={handleChange} className="form-input" required /></div><div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem' }}><button type="button" onClick={onCancel} className="btn" style={{ backgroundColor: 'var(--secondary-color)', color: 'white' }}>Annuler</button><button type="submit" className="btn btn-primary">Enregistrer</button></div></form>) }
    return (<form onSubmit={handleSubmit} className="form-container" style={{ maxWidth: 'none', margin: 0, padding: '2rem' }}><h3>{isCreating ? 'Créer' : 'Modifier'} l'élément</h3>{error && <p className="error-message">{error}</p>}<div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>{Object.entries(formFields).map(([key, type]) => (<div className="form-group" key={key}><label>{columnTranslations[key] || key.replace(/_/g, ' ')}</label>{key === 'password' ? (<PasswordInput name={key} value={formData[key] || ''} onChange={handleChange} placeholder={!isCreating ? 'Laisser vide pour conserver' : ''} required={isCreating} />) : key === 'destination' ? (<><input type="text" name="destination" value={formData.destination || ''} onChange={handleChange} className="form-input" list="destination-datalist-form" placeholder="Choisissez ou créez une destination" autoComplete="off" /><datalist id="destination-datalist-form">{destinations.map(dest => <option key={dest} value={dest} />)}</datalist></>) : type === 'checkbox' ? (<input type="checkbox" name={key} checked={!!formData[key]} onChange={handleChange} className="form-checkbox" />) : (<input type={type} name={key} value={formData[key] || ''} onChange={handleChange} className="form-input" required={key !== 'destination' && key !== 'token' && type !== 'checkbox'} readOnly={(key === 'token')} />)}</div>))}</div><div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem' }}><button type="button" onClick={onCancel} className="btn" style={{ backgroundColor: 'var(--secondary-color)', color: 'white' }}>Annuler</button><button type="submit" className="btn btn-primary">Enregistrer</button></div></form>);
}

function ToolsAndExportPanel({ token, user, adminUsers, userDestinations }) {
    const [filters, setFilters] = useState({ user_id: '', destination: '' });
    const [previewData, setPreviewData] = useState(null);
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteMsg, setInviteMsg] = useState('');
    const [invitationLink, setInvitationLink] = useState('');
    const [notification, setNotification] = useState({ message: '', type: '' });

    const showNotification = (message, type = 'error') => { setNotification({ message, type }); };
    const handleFilterChange = (name, value) => { setFilters(prev => ({ ...prev, [name]: value })); setPreviewData(null); };

    const getFilteredData = async () => {
        const activeFilters = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
        if (user.role !== 'admin') delete activeFilters.user_id;
        const query = new URLSearchParams(activeFilters).toString();
        try {
            const response = await fetch(`${API_URL}/export/data?${query}`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (!response.ok) {
                const err = await response.json();
                showNotification(`Échec de la récupération des données: ${err.detail}`);
                return null;
            }
            return response;
        } catch (error) { showNotification('Une erreur est survenue lors de la récupération des données.'); return null; }
    };

    const handlePreview = async () => {
        const response = await getFilteredData();
        if (response) {
            const csvText = await response.text();
            if (!csvText) { setPreviewData([]); return; }
            const rows = csvText.trim().split('\n');
            const headers = rows[0].split(',');
            const data = rows.slice(1).map(row => { const values = row.split(','); return headers.reduce((obj, h, i) => ({ ...obj, [h]: values[i] }), {}); });
            setPreviewData(data);
        }
    };

    const handleExport = async () => {
        const response = await getFilteredData();
        if (response) {
            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            const filename = contentDisposition?.match(/filename="?(.+)"?/)?.[1] || 'passports_export.csv';
            const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
            setPreviewData(null);
        }
    };

    const handleInvite = async () => {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inviteEmail)) { setInviteMsg('Veuillez entrer une adresse email valide.'); return; }
        setInviteMsg('Génération du lien...'); setInvitationLink('');
        try {
            const response = await fetch(`${API_URL}/admin/invitations`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ email: inviteEmail }), });
            const data = await response.json();
            if (response.ok) { const link = `${window.location.origin}/register/${data.token}`; setInvitationLink(link); setInviteMsg('Lien généré. Copiez-le et envoyez-le à l\'utilisateur.'); } else { setInviteMsg(data.detail || 'Échec de la création de l\'invitation.'); }
        } catch (error) { setInviteMsg('Une erreur est survenue.'); }
    };

    return (
        <div>
            <Notification message={notification.message} type={notification.type} onClear={() => setNotification({ message: '', type: '' })} />
            <h2>Outils & Exportation</h2>
            {user.role === 'admin' && (
                <div className="form-container" style={{ maxWidth: 'none', margin: 0, padding: '2rem', marginBottom: '2rem' }}>
                    <h3>Inviter un nouvel utilisateur</h3>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <input type="email" placeholder="Entrez l'email de l'utilisateur" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} className="form-input" style={{ flexGrow: 1 }} />
                        <button onClick={handleInvite} className="btn btn-primary" style={{ backgroundColor: 'var(--warning-color)', color: 'black' }}>Générer le lien</button>
                    </div>
                    {inviteMsg && <p className="info-message mt-1">{inviteMsg}</p>}
                    {invitationLink && (<div className="mt-1"><input type="text" readOnly value={invitationLink} className="form-input" onClick={e => e.target.select()} /></div>)}
                </div>
            )}
            <div className="form-container" style={{ maxWidth: 'none', margin: 0, padding: '2rem' }}>
                <h3>Filtrer et Exporter les Données des Passeports</h3>
                <div className="filter-bar mb-1">
                    {user.role === 'admin' && (<ComboBoxFilter name="user_id" placeholder="Filtrer par Utilisateur" options={adminUsers} getOptionValue={(o) => o.id} getOptionLabel={(o) => `${o.first_name} ${o.last_name} (${o.user_name})`} onChange={handleFilterChange} />)}
                    <ComboBoxFilter name="destination" placeholder="Filtrer par Destination" options={userDestinations.map(d => ({ destination: d }))} getOptionValue={(o) => o.destination} getOptionLabel={(o) => o.destination} onChange={handleFilterChange} />
                </div>
                <button onClick={handlePreview} className="btn btn-primary">Aperçu des Données</button>
                {previewData && (<><PreviewTable data={previewData} /><button onClick={handleExport} className="btn mt-1" style={{ backgroundColor: 'var(--success-color)', color: 'white' }}>Télécharger en CSV</button></>)}
            </div>
        </div>
    );
}

function ComboBoxFilter({ name, placeholder, options, getOptionValue, getOptionLabel, onChange }) {
    const dataListId = `datalist-${name}-${Math.random()}`;
    return (
        <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
            <input list={dataListId} name={name} placeholder={placeholder} onChange={(e) => onChange(name, e.target.value)} className="form-input" autoComplete="off" />
            <datalist id={dataListId}>
                <option value="">-- Aucun --</option>
                {options.map(option => (<option key={getOptionValue(option)} value={getOptionValue(option)}>{getOptionLabel(option)}</option>))}
            </datalist>
        </div>
    );
}

function PreviewTable({ data }) {
    if (!data || data.length === 0) return <p className="mt-2 text-center info-message">Aucune donnée à prévisualiser pour les filtres sélectionnés.</p>;
    const headers = Object.keys(data[0]);
    return (<div className="mt-2"><h3 className="mb-1">Aperçu des Données</h3><div className="table-container"><table className="table"><thead><tr>{headers.map(h => <th key={h}>{columnTranslations[h] || h.replace(/_/g, ' ')}</th>)}</tr></thead><tbody>{data.map((row, i) => <tr key={i}>{headers.map(h => <td key={h}>{String(row[h])}</td>)}</tr>)}</tbody></table></div></div>);
}