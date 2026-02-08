import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import api from '../../services/api';
import { Megaphone, Calendar, MessageSquare, Plus, Search, Briefcase, FileText } from 'lucide-react';

const DashboardHome = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      if (user?.role === 'ADMIN') {
        const response = await api.get('/admin/stats');
        setStats(response.data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
    setLoading(false);
  };

  const isAdmin = user?.role === 'ADMIN';
  const isPro = user?.role === 'PROFESSIONNEL';
  const isParticulier = user?.role === 'PARTICULIER';

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Welcome header */}
        <div className="bg-gradient-to-r from-purple-600 to-cyan-500 rounded-2xl p-8 text-white">
          <h1 className="text-3xl font-bold mb-2" data-testid="dashboard-welcome">
            Bienvenue, {user?.full_name} !
          </h1>
          <p className="opacity-90">
            {isAdmin 
              ? "Gérez votre plateforme SmartHome depuis votre espace administrateur."
              : isPro 
                ? "Trouvez des missions et développez votre activité."
                : "Gérez vos demandes et rendez-vous depuis votre espace client."}
          </p>
        </div>

        {/* Admin Stats */}
        {isAdmin && stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Utilisateurs"
              value={stats.users.total}
              subtitle={`${stats.users.particuliers} particuliers, ${stats.users.professionnels} pros`}
              icon="👥"
              color="purple"
            />
            <StatCard
              title="Demandes en attente"
              value={stats.requests.pending}
              subtitle={`${stats.requests.total} au total`}
              icon="📋"
              color="cyan"
            />
            <StatCard
              title="RDV à confirmer"
              value={stats.appointments.pending}
              subtitle={`${stats.appointments.confirmed} confirmés`}
              icon="📅"
              color="green"
            />
            <StatCard
              title="Messages non lus"
              value={stats.messages.unread}
              subtitle="À traiter"
              icon="💬"
              color="orange"
            />
          </div>
        )}

        {/* Professional quick actions */}
        {isPro && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <QuickActionCard
              title="Annonces disponibles"
              description="Parcourez les demandes de clients"
              href="/dashboard/annonces"
              icon={<Megaphone className="w-8 h-8 text-purple-600" />}
              highlight={true}
            />
            <QuickActionCard
              title="Mes réponses"
              description="Suivez vos candidatures"
              href="/dashboard/my-responses"
              icon={<FileText className="w-8 h-8 text-cyan-600" />}
            />
            <QuickActionCard
              title="Mon profil pro"
              description="Complétez votre profil entreprise"
              href="/dashboard/company"
              icon={<Briefcase className="w-8 h-8 text-green-600" />}
            />
          </div>
        )}

        {/* Particulier quick actions */}
        {isParticulier && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <QuickActionCard
              title="Nouvelle annonce"
              description="Publiez une demande de service"
              href="/dashboard/my-annonces?new=true"
              icon={<Plus className="w-8 h-8 text-purple-600" />}
            />
            <QuickActionCard
              title="Prendre RDV"
              description="Planifiez un rendez-vous"
              href="/rendez-vous"
              icon={<Calendar className="w-8 h-8 text-cyan-600" />}
            />
            <QuickActionCard
              title="Nous contacter"
              description="Envoyez-nous un message"
              href="/dashboard/messages?new=true"
              icon={<MessageSquare className="w-8 h-8 text-green-600" />}
            />
          </div>
        )}

        {/* User info card */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Informations du compte</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoItem label="Nom complet" value={user?.full_name} />
            <InfoItem label="Email" value={user?.email} />
            <InfoItem label="Téléphone" value={user?.phone || 'Non renseigné'} />
            <InfoItem label="Type de compte" value={user?.role === 'PARTICULIER' ? 'Particulier' : user?.role === 'PROFESSIONNEL' ? 'Professionnel' : 'Administrateur'} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

const StatCard = ({ title, value, subtitle, icon, color }) => {
  const colorClasses = {
    purple: 'bg-purple-100 text-purple-600',
    cyan: 'bg-cyan-100 text-cyan-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <span className={`text-2xl p-3 rounded-lg ${colorClasses[color]}`}>{icon}</span>
        <span className="text-3xl font-bold text-gray-900">{value}</span>
      </div>
      <h3 className="font-medium text-gray-900">{title}</h3>
      <p className="text-sm text-gray-500">{subtitle}</p>
    </div>
  );
};

const QuickActionCard = ({ title, description, href, icon, highlight }) => {
  return (
    <a
      href={href}
      className={`bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-all block border-2 ${highlight ? 'border-purple-200 hover:border-purple-400' : 'border-transparent'}`}
      data-testid={`quick-action-${title.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <span className="mb-4 block">{typeof icon === 'string' ? <span className="text-3xl">{icon}</span> : icon}</span>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500">{description}</p>
    </a>
  );
};

const InfoItem = ({ label, value }) => (
  <div>
    <p className="text-sm text-gray-500">{label}</p>
    <p className="font-medium text-gray-900">{value}</p>
  </div>
);

export default DashboardHome;
