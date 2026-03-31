# Plano Detalhado Arquitetural: Docker, PostgreSQL, Neo4j e Predição Vetorial

Este documento fornece um guia passo a passo **extremamente detalhado** para fazer toda a refatoração manualmente. Você subirá a infraestrutura via Docker, criará as conexões em código JavaScript e migrará a lógica atual de dados JSON para uma arquitetura combinando PostgreSQL (dados crus), Neo4j (vetores) e TensorFlow.js (predição).

---

## Fase 1: Subindo os Bancos de Dados via Docker

Começaremos criando a infraestrutura base de bancos em containers locais usando o `docker-compose`. 

**Passo a Passo:**
1. Na raiz do projeto (`/home/wchida/Documents/projects/ia/ia-aplicada/suggest-product/`), crie um arquivo chamado **`docker-compose.yml`**.
2. Preencha este arquivo com o seguinte conteúdo para subir o Postgres e o Neo4j (certifique-se de usar Neo4j versão `>= 5.13` para suporte nativo as buscas de vetor):

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: ia_postgres
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: rootpassword
      POSTGRES_DB: recommender_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  neo4j:
    image: neo4j:5.14.0
    container_name: ia_neo4j
    environment:
      NEO4J_AUTH: neo4j/neo4jpassword
      # Habilitar apoc se futuramente necessário, mas vector index é nativo no 5.13+
      NEO4J_PLUGINS: '["apoc"]'
      # Config para aceitar conexões remotas se necessário nos drivers
      NEO4J_dbms_default__listen__address: '0.0.0.0'
    ports:
      - "7474:7474"   # Interface Web (Browser)
      - "7687:7687"   # Porta Bolt para o JavaScript Driver
    volumes:
      - neo4jdata:/data
    restart: unless-stopped

volumes:
  pgdata:
  neo4jdata:
```

3. Abra o terminal na mesma pasta e rode: `docker-compose up -d`. Isso baixará as imagens e rodará os dois bancos em plano de fundo.

---

## Fase 2: Instalação das Bibliotecas de Conexão no Node.js

Para que seus scripts em Node.js ou os Workers consigam comunicar com esses bancos, você precisará das libs corretas.

**Passo a Passo:**
1. Execute no terminal, dentro da pasta raiz:
```bash
npm install pg neo4j-driver dotenv
```
*(A lib `dotenv` é opcional, mas boa para gerenciar senhas fora do código fonte).*

---

## Fase 3: Conexão e Migração de Dados para o PostgreSQL

Aqui definiremos o esquema do banco relacional e popularemos a partir de arquivos `.json`. 
Você criará um script isolado `scripts/migrateToPostgres.js`.

**Passo a Passo Manual:**
1. Crie o diretório `/scripts` se não existir, e crie o arquivo `migrateToPostgres.js`.
2. O código de conexão no script deve ser o seguinte:
```javascript
const { Pool } = require('pg');
const fs = require('fs');

const pool = new Pool({
  user: 'root',
  host: 'localhost',
  database: 'recommender_db',
  password: 'rootpassword',
  port: 5432,
});

async function runMigration() {
  const client = await pool.connect();
  try {
    // 1. Criar Tabelas
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        original_id INT,
        name VARCHAR(255),
        age INT
      );
      CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        original_id INT,
        name VARCHAR(255),
        category VARCHAR(255),
        price DECIMAL(10, 2),
        color VARCHAR(255)
      );
      CREATE TABLE IF NOT EXISTS purchases (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        product_id INT REFERENCES products(id)
      );
    `);
    
    // 2. Popular lendo os JSONs (Exemplo Resumido)
    const usersData = JSON.parse(fs.readFileSync('./data/users.json', 'utf8'));
    // Itere pelo usersData e insira usando:
    // await client.query('INSERT INTO users(original_id, name, age) VALUES($1, $2, $3)', [user.id, user.name, user.age]);
    
    console.log("Migração do DB Relacional completa.");
  } finally {
    client.release();
    pool.end();
  }
}

runMigration();
```
3. Execute-o via: `node scripts/migrateToPostgres.js`.

---

## Fase 4: Geração das Embeddings e Migração para o Neo4j

Aqui entraremos na capacidade de Grafos. O Neo4j suporta Vectors nativamente na v5.13+. O objetivo é passar todas as contas matemáticas e as normalizações em `encodeProduct` e gerar as predições de dimensão que o TensorFlow processou.

**Passo a Passo Manual:**
1. Crie um script isolado: `scripts/migrateToNeo4j.js`.
2. Como se conectar ao Neo4j usando a lib que instalamos:
```javascript
const neo4j = require('neo4j-driver');

// Use protocol 'bolt' para Node local
const driver = neo4j.driver(
  'bolt://localhost:7687',
  neo4j.auth.basic('neo4j', 'neo4jpassword')
);

async function runNeo4jMigration() {
  const session = driver.session();
  try {
    // AQUI: Você executa as lógicas Math e TF.js para obter o "productVector"
    // Exemplo simulado de vetor numérico (baseado no seu ctx.dimentision):
    const dimensions = 15; // Defina de acordo com a saída do encodeProduct() do seu projeto

    // 1. Criar o Índice de Busca em Vetor PRIMEIRO
    await session.run(`
      CREATE VECTOR INDEX product_embeddings IF NOT EXISTS
      FOR (p:Product) ON (p.embedding)
      OPTIONS {
        indexConfig: {
          \`vector.dimensions\`: $dim,
          \`vector.similarity_function\`: 'cosine'
        }
      }
    `, { dim: dimensions });

    console.log("Índice de Vetor Criado.");

    // 2. Inserir nós dos Produtos com o seu Embedding Vetorial
    // Digamos que "productVectorArray" é o retorno de encodeProduct(product, ctx).dataSync()
    const productData = { 
        id: "prod_1", 
        name: "Fones de Ouvido Sem Fio", 
        embedding: [0.1, 0.45, 0.2, /*...*/] // Array Float32 convertido pra array JS
    };

    await session.run(`
      MERGE (p:Product {original_id: $id})
      SET p.name = $name,
          p.embedding = $embedding
    `, { 
      id: productData.id, 
      name: productData.name, 
      embedding: productData.embedding 
    });

    console.log("Produto Inserido no Neo4j com vetor completo.");
  } finally {
    await session.close();
    await driver.close();
  }
}

runNeo4jMigration();
```

---

## Fase 5: Integração da Busca Vetorial (Retrieval) no TensorFlow (Worker)

No seu `src/workers/modelTrainingWorker.js`, você não precisa mais comparar o usuário com *todos* os produtos da `data/products.json`. Utilizaremos o Neo4j para recuperar somente os produtos matematicamente parecidos na base do "cosseno" antes de passar ao modelo classificador Neural (*recomendador*).

**Passo a Passo Manual de Refatoração do Fluxo `recommend(user)`**:
1. Conecte ao DB diretamente do node e obtenha o `userVector` usando a função `encodeUser()`.
2. Faça a "Busca K-Nearest Neighbors" (K-NN) utilizando o driver do Neo4j.
Exemplo de Cypher Query de busca (No Neo4j 5.X):
```javascript
const userVectorArray = Array.from(userVector); // converte Float32Array
const k = 10; // Quero os TOP 10 produtos mais parecidos para predição

const response = await session.run(`
  // A sintaxe CALL no Neo4j resolve a similaridade indexada mais rapidamente
  CALL db.index.vector.queryNodes('product_embeddings', $top_k, $vector)
  YIELD node, score
  RETURN node.original_id AS id, node.name AS name, node.embedding AS vector, score
`, { top_k: k, vector: userVectorArray });

// response.records vai retornar os 10 candidatos mais rápidos
```
3. Construa seu **Tensor Input** mesclando os arrays do que o Neo4j devolveu com o usuário:
```javascript
const candidateInputs = response.records.map(r => {
   const prodVector = r.get('vector');
   return [...userVectorArray, ...prodVector];
});
const inputTensor = tf.tensor2d(candidateInputs);
```
4. Aplique seu modelo Neural e Rankeie:
```javascript
const predictions = _model.predict(inputTensor);
const scores = predictions.dataSync(); // Confiança final da Rede Neural
```
5. Envie a resposta ao Frontend no mesmo modelo `workerEvents.recommend`.
