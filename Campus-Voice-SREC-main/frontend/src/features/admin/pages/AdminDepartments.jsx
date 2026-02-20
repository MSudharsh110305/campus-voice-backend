import React from 'react';
import { DEPARTMENT_LIST } from '../../../utils/constants';
import { Card } from '../../../components/UI';
import { Building2, Users, FileText } from 'lucide-react';

export default function AdminDepartments() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Departments Overview</h1>
                <p className="text-gray-500">Manage and monitor departmental performance</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {DEPARTMENT_LIST.map(dept => (
                    <div key={dept.id} className="bg-white rounded-2xl p-6 border border-gray-100 hover:shadow-lg transition-all group cursor-pointer">
                        <div className="flex items-center justify-between mb-6">
                            <div className="w-12 h-12 bg-srec-primary/10 rounded-xl flex items-center justify-center text-srec-primary group-hover:bg-srec-primary group-hover:text-white transition-colors">
                                <Building2 size={24} />
                            </div>
                            <span className="text-xs font-mono text-gray-400">ID: {dept.id}</span>
                        </div>

                        <h3 className="text-xl font-bold text-gray-900 mb-2">{dept.name}</h3>

                        <div className="space-y-3 pt-4 border-t border-gray-50">
                            <div className="flex items-center justify-between text-sm text-gray-600">
                                <span className="flex items-center gap-2"><FileText size={14} /> Complaints</span>
                                <span className="font-semibold">-</span>
                            </div>
                            <div className="flex items-center justify-between text-sm text-gray-600">
                                <span className="flex items-center gap-2"><Users size={14} /> Authorities</span>
                                <span className="font-semibold">-</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
