/**
 * SISTEMA INTEGRA UBS - Componentes Vue.js
 * 
 * Arquivo contendo componentes Vue.js para reutilização no sistema.
 */

// Componente para exibir alerta com mensagem
Vue.component('alert-message', {
    props: {
        type: {
            type: String,
            default: 'info'
        },
        message: {
            type: String,
            required: true
        },
        dismissible: {
            type: Boolean,
            default: true
        }
    },
    template: `
        <div :class="['alert', 'alert-' + type, dismissible ? 'alert-dismissible fade show' : '']" role="alert">
            {{ message }}
            <button v-if="dismissible" type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
        </div>
    `
});

// Componente para seleção de paciente com busca
Vue.component('patient-selector', {
    props: {
        patients: {
            type: Array,
            required: true
        },
        selectedId: {
            type: Number,
            default: null
        }
    },
    data() {
        return {
            searchTerm: '',
            selectedPatient: null
        }
    },
    computed: {
        filteredPatients() {
            if (!this.searchTerm) return this.patients;
            
            const searchLower = this.searchTerm.toLowerCase();
            return this.patients.filter(patient => {
                return patient.nome.toLowerCase().includes(searchLower) || 
                       (patient.cpf && patient.cpf.includes(searchLower)) ||
                       (patient.sus_card && patient.sus_card.includes(searchLower));
            });
        }
    },
    methods: {
        selectPatient(patient) {
            this.selectedPatient = patient;
            this.$emit('patient-selected', patient.id);
        }
    },
    mounted() {
        if (this.selectedId) {
            const patient = this.patients.find(p => p.id === this.selectedId);
            if (patient) {
                this.selectedPatient = patient;
            }
        }
    },
    template: `
        <div class="patient-selector">
            <div class="input-group mb-3">
                <input type="text" class="form-control" v-model="searchTerm" placeholder="Buscar paciente por nome, CPF ou cartão SUS">
                <button class="btn btn-outline-secondary" type="button" data-bs-toggle="modal" data-bs-target="#patientSelectorModal">
                    <i class="fas fa-search"></i>
                </button>
            </div>
            
            <div v-if="selectedPatient" class="selected-patient p-3 border rounded mb-3">
                <h6 class="mb-1">Paciente Selecionado</h6>
                <p class="mb-0"><strong>{{ selectedPatient.nome }}</strong></p>
                <p class="mb-0 small text-muted" v-if="selectedPatient.cpf">CPF: {{ selectedPatient.cpf }}</p>
                <input type="hidden" name="patient_id" :value="selectedPatient.id">
            </div>
            
            <!-- Modal de seleção de paciente -->
            <div class="modal fade" id="patientSelectorModal" tabindex="-1" aria-labelledby="patientSelectorModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="patientSelectorModalLabel">Selecionar Paciente</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
                        </div>
                        <div class="modal-body">
                            <div class="input-group mb-3">
                                <input type="text" class="form-control" v-model="searchTerm" placeholder="Buscar paciente por nome, CPF ou cartão SUS">
                                <button class="btn btn-outline-secondary" type="button">
                                    <i class="fas fa-search"></i>
                                </button>
                            </div>
                            
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Nome</th>
                                            <th>CPF</th>
                                            <th>Data de Nascimento</th>
                                            <th>Cartão SUS</th>
                                            <th></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="patient in filteredPatients" :key="patient.id">
                                            <td>{{ patient.nome }}</td>
                                            <td>{{ patient.cpf || '-' }}</td>
                                            <td>{{ patient.data_nascimento || '-' }}</td>
                                            <td>{{ patient.sus_card || '-' }}</td>
                                            <td>
                                                <button type="button" class="btn btn-sm btn-primary" @click="selectPatient(patient)" data-bs-dismiss="modal">
                                                    Selecionar
                                                </button>
                                            </td>
                                        </tr>
                                        <tr v-if="filteredPatients.length === 0">
                                            <td colspan="5" class="text-center">Nenhum paciente encontrado</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
});

// Componente para listar itens de prescrição com adição dinâmica
Vue.component('prescription-items', {
    props: {
        medications: {
            type: Array,
            required: true
        }
    },
    data() {
        return {
            items: [{
                medication_id: '',
                quantidade: 1,
                instrucoes: ''
            }]
        }
    },
    methods: {
        addItem() {
            this.items.push({
                medication_id: '',
                quantidade: 1,
                instrucoes: ''
            });
        },
        removeItem(index) {
            if (this.items.length > 1) {
                this.items.splice(index, 1);
            }
        },
        getMedicationName(id) {
            const medication = this.medications.find(m => m.id == id);
            return medication ? medication.nome : '';
        }
    },
    template: `
        <div class="prescription-items">
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Medicamento</th>
                            <th>Quantidade</th>
                            <th>Instruções</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(item, index) in items" :key="index">
                            <td>
                                <select class="form-select" v-model="item.medication_id" :name="'medication_id[]'" required>
                                    <option value="">Selecione um medicamento</option>
                                    <option v-for="med in medications" :key="med.id" :value="med.id">
                                        {{ med.nome }} {{ med.concentracao ? '- ' + med.concentracao : '' }}
                                    </option>
                                </select>
                            </td>
                            <td>
                                <input type="number" class="form-control" v-model="item.quantidade" :name="'quantidade[]'" min="1" required>
                            </td>
                            <td>
                                <input type="text" class="form-control" v-model="item.instrucoes" :name="'instrucoes[]'" placeholder="Ex: 1 comprimido a cada 8h">
                            </td>
                            <td>
                                <button type="button" class="btn btn-sm btn-danger" @click="removeItem(index)" :disabled="items.length === 1">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="text-end">
                <button type="button" class="btn btn-primary" @click="addItem">
                    <i class="fas fa-plus"></i> Adicionar Medicamento
                </button>
            </div>
        </div>
    `
});