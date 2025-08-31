from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
import asyncio
import os
from datetime import datetime
import logging

from ...llm.engine import LLMEngine
from ...embeddings.embedding import ONNXEmbedder
from ...vectorstore.faiss_store import LocalFaiss
from ...npu_monitor import npu_monitor, monitor_inference
from ...security.policies import Policy

log = logging.getLogger(__name__)


class OnboardingAgent:
    """
    Agente de Onboarding com IA real que:
    - Detecta intenção usando análise semântica
    - Faz perguntas inteligentes usando LLM
    - Coleta contexto pessoal do usuário via chat
    - Indexa informações no FAISS com embeddings reais
    - Permite que todos os agentes acessem o contexto
    """

    def __init__(self, llm_engine: LLMEngine, embedder: ONNXEmbedder, vector_store: LocalFaiss):
        self.llm = llm_engine
        self.embedder = embedder
        self.vector_store = vector_store
        self.conversation_history: List[Dict[str, str]] = []

        # Diretórios para dados de usuários
        self.users_dir = "./data/users"
        self.user_indexes_dir = "./data/user_indexes"

        # Garantir que diretórios existam
        os.makedirs(self.users_dir, exist_ok=True)
        os.makedirs(self.user_indexes_dir, exist_ok=True)

        # Estado da conversa de onboarding
        self.onboarding_state = {
            "current_step": "greeting",
            "collected_info": {},
            "pending_questions": [],
            "conversation_context": ""
        }

        # Inicializar monitoramento NPU
        npu_monitor.start_monitoring()

    async def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Processa mensagem do usuário e avança no onboarding usando IA real
        """
        log.info(f"💬 Processando mensagem do usuário {user_id}: {message[:50]}...")

        # Adicionar mensagem ao histórico
        self.conversation_history.append({"role": "user", "content": message})

        # Detectar intenção usando IA
        with monitor_inference():
            intent = self._detect_intent(message)

        # Atualizar estado da conversa
        self.onboarding_state["conversation_context"] += f"\nUsuário: {message}"

        # Processar baseado na intenção detectada
        if intent == "first_access":
            return self._start_onboarding_flow(user_id, message)
        elif intent == "continue_onboarding":
            return self._continue_onboarding_flow(user_id, message)
        elif intent == "already_onboarded":
            return self._handle_existing_user(user_id)
        else:
            return self._handle_general_query(user_id, message, intent)

    async def _detect_intent(self, message: str) -> str:
        """
        Detecta intenção da mensagem usando análise semântica com LLM
        """
        intent_prompt = f"""
        Analise esta mensagem do usuário e determine a intenção principal:

        Mensagem: "{message}"

        Contexto da conversa anterior:
        {self.onboarding_state.get("conversation_context", "")}

        Classifique em uma das seguintes intenções:

        1. "first_access" - Usuário está fazendo primeiro acesso, quer começar onboarding
        2. "continue_onboarding" - Usuário está respondendo perguntas do onboarding
        3. "already_onboarded" - Usuário já tem perfil e quer acessar funcionalidades
        4. "general_help" - Usuário precisa de ajuda geral ou tem dúvida

        Considere palavras-chave como:
        - Primeiro acesso: "primeiro", "novo", "começar", "iniciar", "olá", "bem-vindo"
        - Já cadastrado: "já tenho", "meu perfil", "já fiz", "continuar"
        - Respostas: informações pessoais, profissionais, preferências

        Responda apenas com a classificação (uma palavra).
        """

        try:
            response = self.llm.generate_text(intent_prompt, max_length=50)
            response = response.strip().lower()

            # Mapear resposta para intenções válidas
            if "first_access" in response or "primeiro" in response:
                return "first_access"
            elif "continue" in response or "resposta" in response:
                return "continue_onboarding"
            elif "already" in response or "perfil" in response:
                return "already_onboarded"
            else:
                return "general_help"

        except Exception as e:
            log.warning(f"Erro na detecção de intenção: {e}")
            # Fallback: analisar manualmente
            return self._fallback_intent_detection(message)

    def _fallback_intent_detection(self, message: str) -> str:
        """
        Fallback para detecção de intenção sem LLM
        """
        message_lower = message.lower()

        # Palavras-chave para primeiro acesso
        first_access_keywords = [
            "primeiro acesso", "primeira vez", "novo usuário", "nova conta",
            "começar", "iniciar", "bem vindo", "olá", "oi", "boa tarde",
            "não tenho conta", "sou novo", "nova aqui", "novo aqui"
        ]

        # Palavras-chave para usuário existente
        existing_keywords = [
            "já tenho", "meu perfil", "já fiz", "continuar", "já cadastrei"
        ]

        if any(keyword in message_lower for keyword in first_access_keywords):
            return "first_access"
        elif any(keyword in message_lower for keyword in existing_keywords):
            return "already_onboarded"
        else:
            return "continue_onboarding"

    async def _start_onboarding_flow(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Inicia fluxo completo de onboarding
        """
        log.info(f"🚀 Iniciando onboarding para usuário: {user_id}")

        # Verificar se já existe perfil
        if self._user_exists(user_id):
            # Oferecer carregar perfil existente ou recriar
            return self._handle_existing_profile_choice(user_id)

        # Resetar estado do onboarding
        self.onboarding_state = {
            "current_step": "greeting",
            "collected_info": {},
            "pending_questions": [],
            "conversation_context": f"Usuário iniciou onboarding: {message}"
        }

        # Iniciar com saudação
        greeting_response = self._generate_greeting_response(user_id)

        return {
            "response": greeting_response,
            "onboarding_status": "started",
            "next_step": "ask_name",
            "user_id": user_id,
            "requires_user_input": True
        }

    async def _continue_onboarding_flow(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Continua o fluxo de onboarding baseado no estado atual
        """
        current_step = self.onboarding_state.get("current_step", "greeting")

        # Processar resposta baseado na etapa atual
        if current_step == "ask_name":
            return self._process_name_response(user_id, message)
        elif current_step == "ask_profession":
            return self._process_profession_response(user_id, message)
        elif current_step == "ask_preferences":
            return self._process_preferences_response(user_id, message)
        elif current_step == "complete":
            return self._finalize_onboarding(user_id)
        else:
            # Detectar automaticamente o que perguntar
            return self._generate_next_question(user_id, message)

    async def _handle_existing_user(self, user_id: str) -> Dict[str, Any]:
        """
        Trata usuário que já tem perfil
        """
        if self._user_exists(user_id):
            user_context = self._load_user_context(user_id)
            return {
                "response": f"Olá! Bem-vindo de volta. Seu perfil já está configurado.",
                "user_context": user_context,
                "onboarding_status": "already_completed",
                "user_id": user_id
            }
        else:
            return await self._start_onboarding_flow(user_id, "Olá")

    async def _handle_general_query(self, user_id: str, message: str, intent: str) -> Dict[str, Any]:
        """
        Trata consultas gerais durante ou fora do onboarding
        """
        # Verificar se estamos no meio do onboarding
        if self.onboarding_state.get("current_step") not in ["greeting", "complete"]:
            # Estamos no meio do onboarding, processar como resposta
            return await self._continue_onboarding_flow(user_id, message)

        # Consulta geral - tentar detectar se é sobre onboarding
        if "onboarding" in message.lower() or "cadastro" in message.lower():
            return await self._start_onboarding_flow(user_id, message)

        # Resposta genérica
        return {
            "response": "Olá! Sou o assistente de integração Itaú. Posso ajudar você com o processo de cadastro ou acessar suas funcionalidades já configuradas.",
            "onboarding_status": "general_help",
            "user_id": user_id
        }

    async def _generate_greeting_response(self, user_id: str) -> str:
        """
        Gera resposta de saudação personalizada usando LLM
        """
        greeting_prompt = f"""
        Você é o assistente de integração do Itaú. Um usuário (ID: {user_id})
        está fazendo seu primeiro acesso ao sistema.

        Crie uma saudação acolhedora e profissional que:
        1. Demonstre conhecimento do contexto Itaú
        2. Explique brevemente o propósito do onboarding
        3. Incentive o usuário a fornecer informações
        4. Mantenha tom amigável mas profissional

        A saudação deve preparar o usuário para responder perguntas sobre:
        - Informações pessoais básicas
        - Perfil profissional
        - Preferências de uso

        Máximo 150 palavras.
        """

        greeting = self.llm.generate_text(greeting_prompt, max_length=150)

        # Adicionar ao histórico
        self.conversation_history.append({"role": "assistant", "content": greeting})

        return greeting.strip()

    async def _generate_next_question(self, user_id: str, user_response: str) -> Dict[str, Any]:
        """
        Gera próxima pergunta inteligente baseada na resposta anterior usando LLM
        """
        # Analisar informações já coletadas
        collected_info = self.onboarding_state.get("collected_info", {})

        question_prompt = f"""
        Você é especialista em onboarding Itaú. Baseado nas informações já coletadas
        e na última resposta do usuário, determine qual é a próxima pergunta mais
        relevante e útil para fazer.

        Informações já coletadas:
        {json.dumps(collected_info, indent=2, ensure_ascii=False)}

        Última resposta do usuário: "{user_response}"

        Contexto da conversa:
        {self.onboarding_state.get("conversation_context", "")}

        Decida qual informação ainda precisamos coletar:
        1. Se ainda não temos nome → perguntar nome
        2. Se ainda não temos informações profissionais → perguntar cargo/área
        3. Se ainda não temos preferências → perguntar sites/ferramentas
        4. Se temos informações básicas → perguntar sobre experiência específica
        5. Se temos tudo básico → finalizar com pergunta sobre objetivos

        Gere uma pergunta natural e contextualizada que ajude a personalizar
        a experiência Itaú do usuário.

        Responda apenas com a pergunta, sem explicações adicionais.
        """

        try:
            next_question = self.llm.generate_text(question_prompt, max_length=100)

            # Identificar tipo da pergunta para atualizar estado
            question_type = self._classify_question_type(next_question, collected_info)

            # Atualizar estado
            self.onboarding_state["current_step"] = question_type
            self.onboarding_state["last_question"] = next_question

            # Adicionar pergunta ao histórico
            self.conversation_history.append({"role": "assistant", "content": next_question})

            return {
                "response": next_question.strip(),
                "onboarding_status": "in_progress",
                "question_type": question_type,
                "user_id": user_id,
                "requires_user_input": True
            }

        except Exception as e:
            log.error(f"Erro ao gerar próxima pergunta: {e}")
            return await self._fallback_question_generation(user_id, collected_info)

    async def _classify_question_type(self, question: str, collected_info: Dict) -> str:
        """
        Classifica o tipo da pergunta gerada usando LLM
        """
        classify_prompt = f"""
        Classifique esta pergunta de onboarding em uma categoria:

        Pergunta: "{question}"

        Informações já coletadas: {list(collected_info.keys())}

        Categorias:
        - "ask_name" - Pergunta sobre nome ou identificação
        - "ask_personal" - Pergunta sobre informações pessoais (idade, localização)
        - "ask_profession" - Pergunta sobre cargo, área, experiência profissional
        - "ask_experience" - Pergunta sobre experiência específica no Itaú
        - "ask_preferences" - Pergunta sobre preferências de uso, sites, ferramentas
        - "ask_goals" - Pergunta sobre objetivos ou necessidades específicas
        - "finalize" - Momento de finalizar o onboarding

        Responda apenas com a categoria.
        """

        try:
            response = self.llm.generate_text(classify_prompt, max_length=30)
            category = response.strip().lower()

            # Mapear para categorias válidas
            valid_categories = [
                "ask_name", "ask_personal", "ask_profession",
                "ask_experience", "ask_preferences", "ask_goals", "finalize"
            ]

            for cat in valid_categories:
                if cat in category:
                    return cat

            return "ask_general"

        except Exception as e:
            log.warning(f"Erro na classificação: {e}")
            return "ask_general"

    def _fallback_question_generation(self, user_id: str, collected_info: Dict) -> Dict[str, Any]:
        """
        Geração de pergunta fallback quando LLM falha
        """
        questions = []

        if "nome" not in collected_info:
            questions.append(("Qual seu nome completo?", "ask_name"))
        elif "cargo" not in collected_info:
            questions.append(("Qual seu cargo atual no Itaú?", "ask_profession"))
        elif "area" not in collected_info:
            questions.append(("Em qual área você trabalha?", "ask_profession"))
        elif "sites_frequentes" not in collected_info:
            questions.append(("Quais sites/portais você mais acessa no trabalho?", "ask_preferences"))
        else:
            questions.append(("Qual seu objetivo principal ao usar o sistema Itaú?", "ask_goals"))

        question, qtype = questions[0]

        return {
            "response": question,
            "onboarding_status": "in_progress",
            "question_type": qtype,
            "user_id": user_id,
            "requires_user_input": True
        }

    async def _handle_existing_profile_choice(self, user_id: str) -> Dict[str, Any]:
        """
        Trata escolha do usuário sobre perfil existente
        """
        return {
            "response": f"Encontrei um perfil existente para você ({user_id}). Deseja carregar o perfil existente ou criar um novo?",
            "onboarding_status": "profile_choice",
            "user_id": user_id,
            "requires_user_input": True,
            "options": ["carregar", "novo"]
        }

    async def _process_name_response(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Processa resposta sobre nome usando LLM para extrair informação
        """
        extract_prompt = f"""
        Extraia o nome completo da seguinte mensagem do usuário:

        Mensagem: "{message}"

        Se houver um nome completo, responda apenas com o nome.
        Se não houver nome claro, responda com "NOME_NAO_ENCONTRADO".
        """

        try:
            extracted_name = self.llm.generate_text(extract_prompt, max_length=50)
            extracted_name = extracted_name.strip()

            if "NOME_NAO_ENCONTRADO" in extracted_name:
                # Pedir novamente
                return self._ask_for_clarification(user_id, "nome", message)

            # Salvar nome
            self.onboarding_state["collected_info"]["nome"] = extracted_name
            self.onboarding_state["conversation_context"] += f"\nNome identificado: {extracted_name}"

            # Próxima pergunta
            return self._generate_next_question(user_id, message)

        except Exception as e:
            log.error(f"Erro ao processar resposta de nome: {e}")
            return await self._generate_next_question(user_id, message)

    async def _process_profession_response(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Processa resposta sobre informações profissionais
        """
        extract_prompt = f"""
        Analise esta resposta sobre informações profissionais e extraia:
        - Cargo
        - Área de atuação
        - Anos de experiência
        - Principais atividades

        Resposta do usuário: "{message}"

        Formate como JSON válido com as chaves: cargo, area, experiencia_anos, atividades.
        Se alguma informação não estiver clara, use "NAO_INFORMADO".
        """

        try:
            response = self.llm.generate_text(extract_prompt, max_length=200)

            # Tentar extrair JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                prof_info = json.loads(json_match.group())

                # Salvar informações
                collected = self.onboarding_state["collected_info"]
                collected.update(prof_info)
                self.onboarding_state["conversation_context"] += f"\nInformações profissionais: {prof_info}"

                # Próxima pergunta
                return await self._generate_next_question(user_id, message)
            else:
                return await self._ask_for_clarification(user_id, "profissional", message)

        except Exception as e:
            log.error(f"Erro ao processar resposta profissional: {e}")
            return await self._generate_next_question(user_id, message)

    async def _process_preferences_response(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Processa resposta sobre preferências
        """
        extract_prompt = f"""
        Analise esta resposta sobre preferências de uso e extraia:
        - Sites/portais frequentes
        - Ferramentas favoritas
        - Tipo de conteúdo preferido
        - Formato preferido
        - Horário de pico

        Resposta do usuário: "{message}"

        Formate como JSON válido.
        """

        try:
            response = self.llm.generate_text(extract_prompt, max_length=200)

            # Tentar extrair JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                pref_info = json.loads(json_match.group())

                # Salvar informações
                collected = self.onboarding_state["collected_info"]
                collected.update(pref_info)
                self.onboarding_state["conversation_context"] += f"\nPreferências: {pref_info}"

                # Próxima pergunta ou finalizar
                return await self._check_completion_and_finalize(user_id)
            else:
                return await self._ask_for_clarification(user_id, "preferências", message)

        except Exception as e:
            log.error(f"Erro ao processar resposta de preferências: {e}")
            return await self._check_completion_and_finalize(user_id)

    async def _ask_for_clarification(self, user_id: str, topic: str, original_message: str) -> Dict[str, Any]:
        """
        Pede esclarecimento quando resposta não está clara
        """
        clarification_prompt = f"""
        O usuário deu uma resposta que não está clara sobre {topic}.
        Resposta original: "{original_message}"

        Gere uma pergunta de esclarecimento amigável e específica
        que ajude o usuário a fornecer a informação necessária.
        """

        try:
            clarification = self.llm.generate_text(clarification_prompt, max_length=100)

            return {
                "response": clarification.strip(),
                "onboarding_status": "clarification_needed",
                "clarification_topic": topic,
                "user_id": user_id,
                "requires_user_input": True
            }
        except Exception as e:
            return {
                "response": f"Poderia esclarecer melhor sobre {topic}?",
                "onboarding_status": "clarification_needed",
                "user_id": user_id,
                "requires_user_input": True
            }

    async def _check_completion_and_finalize(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica se temos informações suficientes para finalizar
        """
        collected = self.onboarding_state["collected_info"]

        # Verificar informações essenciais
        essential_fields = ["nome", "cargo", "area"]
        missing_fields = [field for field in essential_fields if field not in collected]

        if missing_fields:
            # Ainda falta informação essencial
            return await self._generate_next_question(user_id, "continuar")

        # Temos informações suficientes - finalizar
        return await self._finalize_onboarding(user_id)

    async def _finalize_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        Finaliza o processo de onboarding
        """
        log.info(f"🎉 Finalizando onboarding para {user_id}")

        # Criar perfil completo
        profile = self._create_complete_profile(user_id)

        # Salvar perfil
        self._save_user_profile(profile)

        # Indexar no FAISS
        self._index_user_profile(profile)

        # Preparar contexto para outros agentes
        user_context = self._prepare_user_context(profile)

        # Mensagem de conclusão
        completion_message = self._generate_completion_message(profile)

        return {
            "response": completion_message,
            "onboarding_status": "completed",
            "user_id": user_id,
            "user_context": user_context,
            "user_profile": profile,
            "requires_user_input": False
        }

    async def _create_complete_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Cria perfil completo baseado nas informações coletadas
        """
        collected = self.onboarding_state["collected_info"]

        # Organizar em estrutura padrão
        profile = {
            "user_id": user_id,
            "personal_info": {
                "nome": collected.get("nome", ""),
                "idade": collected.get("idade", ""),
                "localizacao": collected.get("localizacao", ""),
                "experiencia_bancaria": collected.get("experiencia_bancaria", "")
            },
            "professional_info": {
                "cargo": collected.get("cargo", ""),
                "area": collected.get("area", ""),
                "experiencia_anos": collected.get("experiencia_anos", ""),
                "principais_atividades": collected.get("principais_atividades", ""),
                "nivel_acesso": collected.get("nivel_acesso", "")
            },
            "preferences": {
                "sites_frequentes": collected.get("sites_frequentes", ""),
                "ferramentas_favoritas": collected.get("ferramentas_favoritas", ""),
                "tipo_conteudo": collected.get("tipo_conteudo", ""),
                "formato_preferido": collected.get("formato_preferido", ""),
                "horario_pico": collected.get("horario_pico", "")
            },
            "usage_patterns": self._estimate_usage_patterns(
                profile["professional_info"],
                profile["preferences"]
            ),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "onboarding_version": "3.0",  # Versão com IA real completa
            "ai_generated": True,
            "conversation_history": self.conversation_history
        }

        return profile

    async def _estimate_usage_patterns(self, professional_info: Dict, preferences: Dict) -> Dict[str, Any]:
        """Estima padrões de uso usando LLM"""
        patterns_prompt = f"""
        Você é analista de comportamento de usuários Itaú.
        Com base neste perfil profissional:

        Cargo: {professional_info["cargo"]}
        Área: {professional_info["area"]}
        Experiência: {professional_info["experiencia_anos"]} anos
        Atividades: {professional_info["principais_atividades"]}
        Horário pico: {preferences["horario_pico"]}

        Estime padrões de uso típicos incluindo:
        - Frequência de uso
        - Tipos de operações realizadas
        - Prioridades no trabalho
        - Horários de atividade

        Formate como JSON válido.
        """

        try:
            patterns_text = self.llm.generate_text(patterns_prompt, max_length=400)

            # Tentar extrair JSON da resposta
            import re
            json_match = re.search(r'\{.*\}', patterns_text, re.DOTALL)
            if json_match:
                patterns = json.loads(json_match.group())
            else:
                # Fallback
                patterns = {
                    "frequencia_uso": "diario",
                    "tipo_operacoes": ["pesquisa_regulatoria"],
                    "prioridades": ["conformidade"],
                    "horarios_atividade": ["09:00-18:00"]
                }

        except Exception as e:
            log.warning(f"Erro ao estimar padrões: {e}")
            patterns = {
                "frequencia_uso": "diario",
                "tipo_operacoes": ["pesquisa_regulatoria"],
                "prioridades": ["conformidade"],
                "horarios_atividade": ["09:00-18:00"]
            }

        return patterns

    async def _generate_completion_message(self, profile: Dict) -> str:
        """
        Gera mensagem de conclusão personalizada
        """
        completion_prompt = f"""
        Você é assistente Itaú. O usuário {profile["personal_info"]["nome"]}
        ({profile["professional_info"]["cargo"]} da área {profile["professional_info"]["area"]})
        acabou de completar o onboarding.

        Crie uma mensagem de conclusão que:
        1. Agradeça pela participação
        2. Destaque que o sistema está personalizado
        3. Mencione próximos passos
        4. Incentive o uso das funcionalidades

        Mantenha tom profissional e acolhedor.
        Máximo 200 palavras.
        """

        completion = self.llm.generate_text(completion_prompt, max_length=200)
        return completion.strip()

    async def _save_user_profile(self, profile: Dict[str, Any]):
        """Salva perfil do usuário em arquivo JSON"""
        user_file = f"{self.users_dir}/{profile['user_id']}.json"

        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

        log.info(f"💾 Perfil salvo: {user_file}")

    async def _index_user_profile(self, profile: Dict[str, Any]):
        """Indexa perfil do usuário no FAISS usando embeddings reais"""
        user_id = profile["user_id"]

        # Preparar documentos para indexação
        documents = self._prepare_documents_for_indexing(profile)

        # Indexar cada documento
        for doc in documents:
            try:
                # Gerar embedding real do conteúdo
                content = doc["content"]
                embedding = self.embedder.embed([content])[0]

                # Adicionar ao vector store com metadata
                metadata = {
                    "user_id": user_id,
                    "doc_type": doc["type"],
                    "category": doc["category"],
                    "timestamp": datetime.now().isoformat()
                }

                # Adicionar ao FAISS
                self.vector_store.add(embedding.reshape(1, -1), [content], [metadata])

                log.info(f"✅ Documento indexado: {doc['type']}")

            except Exception as e:
                log.error(f"❌ Erro ao indexar {doc['type']}: {e}")

    def _prepare_documents_for_indexing(self, profile: Dict) -> List[Dict[str, Any]]:
        """Prepara documentos estruturados para indexação"""
        documents = []

        # 1. Documento de informações pessoais
        personal_doc = {
            "type": "personal_info",
            "category": "personal",
            "content": f"""
            Informações pessoais de {profile["personal_info"]["nome"]}:
            - Nome: {profile["personal_info"]["nome"]}
            - Idade: {profile["personal_info"]["idade"]}
            - Localização: {profile["personal_info"]["localizacao"]}
            - Experiência bancária: {profile["personal_info"]["experiencia_bancaria"]}
            """
        }
        documents.append(personal_doc)

        # 2. Documento de informações profissionais
        prof_doc = {
            "type": "professional_info",
            "category": "professional",
            "content": f"""
            Informações profissionais de {profile["personal_info"]["nome"]}:
            - Cargo: {profile["professional_info"]["cargo"]}
            - Área: {profile["professional_info"]["area"]}
            - Experiência: {profile["professional_info"]["experiencia_anos"]} anos
            - Atividades principais: {profile["professional_info"]["principais_atividades"]}
            - Nível de acesso: {profile["professional_info"]["nivel_acesso"]}
            """
        }
        documents.append(prof_doc)

        # 3. Documento de preferências
        pref_doc = {
            "type": "preferences",
            "category": "preferences",
            "content": f"""
            Preferências de uso de {profile["personal_info"]["nome"]}:
            - Sites frequentes: {profile["preferences"]["sites_frequentes"]}
            - Ferramentas favoritas: {profile["preferences"]["ferramentas_favoritas"]}
            - Tipo de conteúdo: {profile["preferences"]["tipo_conteudo"]}
            - Formato preferido: {profile["preferences"]["formato_preferido"]}
            - Horário de pico: {profile["preferences"]["horario_pico"]}
            """
        }
        documents.append(pref_doc)

        return documents

    async def _prepare_user_context(self, profile: Dict) -> Dict[str, Any]:
        """Prepara contexto do usuário para outros agentes"""
        return {
            "user_id": profile["user_id"],
            "personal_info": profile["personal_info"],
            "professional_info": profile["professional_info"],
            "preferences": profile["preferences"],
            "usage_patterns": profile["usage_patterns"],
            "context_summary": self._generate_context_summary(profile),
            "last_updated": profile["updated_at"]
        }

    async def _generate_context_summary(self, profile: Dict) -> str:
        """Gera resumo inteligente do contexto usando LLM"""
        summary_prompt = f"""
        Você é assistente Itaú especializado em análise de perfis de usuário.
        Crie um resumo executivo conciso do perfil deste usuário:

        NOME: {profile["personal_info"]["nome"]}
        CARGO: {profile["professional_info"]["cargo"]}
        ÁREA: {profile["professional_info"]["area"]}
        EXPERIÊNCIA: {profile["professional_info"]["experiencia_anos"]} anos
        PREFERÊNCIAS: {profile["preferences"]["tipo_conteudo"]}

        O resumo deve ser útil para outros agentes personalizarem atendimento.
        Máximo 200 caracteres.
        """

        summary = self.llm.generate_text(summary_prompt, max_length=100)
        return summary.strip()

    async def _user_exists(self, user_id: str) -> bool:
        """Verifica se usuário já tem perfil salvo"""
        user_file = f"{self.users_dir}/{user_id}.json"
        return os.path.exists(user_file)

    async def _load_user_context(self, user_id: str) -> Dict[str, Any]:
        """Carrega contexto do usuário do arquivo"""
        user_file = f"{self.users_dir}/{user_id}.json"

        if not os.path.exists(user_file):
            return {}

        with open(user_file, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        return await self._prepare_user_context(profile)

    async def get_user_context_for_agents(self, user_id: str, query: str = "") -> Dict[str, Any]:
        """
        Método principal para outros agentes obterem contexto do usuário.
        Inclui busca inteligente no RAG se houver query.
        """
        if not self._user_exists(user_id):
            return {"error": "Usuário não encontrado"}

        # Carregar perfil básico
        context = self._load_user_context(user_id)

        # Se há query, fazer busca inteligente no RAG
        if query and self.vector_store:
            try:
                # Gerar embedding da query
                query_embedding = self.embedder.embed([query])[0]

                # Buscar documentos relevantes do usuário
                results = self.vector_store.search(query_embedding.reshape(1, -1), k=5)

                # Filtrar apenas documentos deste usuário
                user_docs = []
                for doc, score in results:
                    # Verificar se documento pertence ao usuário (simulação)
                    if user_id in doc.lower():
                        user_docs.append({"content": doc, "score": score})

                context["relevant_docs"] = user_docs[:3]  # Top 3 mais relevantes

            except Exception as e:
                log.warning(f"Erro na busca RAG: {e}")

        return context


async def run(state: Dict[str, Any], llm_engine: LLMEngine, embedder: ONNXEmbedder) -> Dict[str, Any]:
    """
    Função principal do Onboarding Agent - ponto de entrada para o graph
    """
    # Inicializar componentes de IA
    vector_store = LocalFaiss(dim=768, index_dir="./data/user_indexes")

    # Criar agente de onboarding
    onboarding_agent = OnboardingAgent(llm_engine, embedder, vector_store)

    # Processar mensagem do usuário
    user_id = state.get("user_id", "unknown_user")
    message = state.get("message", "")

    if not message and not state.get("first_access", False):
        return {
            "response": "Olá! Como posso ajudar você hoje?",
            "onboarding_status": "general_help",
            "user_id": user_id
        }

    # Processar a mensagem
    result = await onboarding_agent.process_message(user_id, message)

    return result
