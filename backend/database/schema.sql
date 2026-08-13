
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','manager') DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE upload_history (

    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT NOT NULL,

    original_filename VARCHAR(255) NOT NULL,

    stored_filename VARCHAR(255) NOT NULL UNIQUE,

    total_data INT,

    status ENUM('UPLOADING','SUCCESS','FAILED') DEFAULT 'UPLOADING',

    uploaded_at DATETIME,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id)
        REFERENCES users(id)

);

CREATE TABLE kategori (

    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    kode VARCHAR(20)NOT NULL UNIQUE,

    nama VARCHAR(100) NOT NULL,

    tipe_formulir ENUM('CAPEX','OPEX')NOT NULL


);

CREATE TABLE budget (

    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    kategori_id BIGINT NOT NULL,

    periode VARCHAR(30),

    nominal DECIMAL(18,2)NOT NULL,

    created_by BIGINT,

    upload_id BIGINT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY(kategori_id)
        REFERENCES kategori(id),

    FOREIGN KEY(created_by)
        REFERENCES users(id),

    FOREIGN KEY(upload_id)
        REFERENCES upload_history(id),

    UNIQUE(kategori_id,periode)

);


CREATE TABLE pr_po_data (

    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    upload_id BIGINT,

    requisition_id VARCHAR(100),

    pr_doc_num VARCHAR(100),

    po_doc_num VARCHAR(100),

    request_date DATE,

    order_date DATE,

    description TEXT,

    comment_text TEXT,

    supplier_name VARCHAR(255),

    qty DECIMAL(15,2),

    uom VARCHAR(20),

    unit_price DECIMAL(18,2),

    total_price DECIMAL(18,2),

    gr_legal_number VARCHAR(100),

    packing_slip VARCHAR(100),

    receipt_date DATE,

    invoice VARCHAR(100),

    invoice_date DATE,

    pr_status VARCHAR(100),

    po_status VARCHAR(100),

    non_stock_item BOOLEAN,

    kategori_id BIGINT NULL,

    budget_id BIGINT NULL,
    
    planning_detail_id BIGINT NULL,

    status_ai ENUM(
        'WAITING',
        'PROCESSING',
        'DONE',
        'FAILED',
        'NEED_MAPPING'
    ) DEFAULT 'WAITING',
    
    budget_status ENUM(
        'ON_PLAN',
        'OVER_PLAN',
        'UNDER_PLAN'
    ) NULL,
    
    layer_klasifikasi TINYINT COMMENT '1=Rule Base, 2=Regex, 3=SVM',
    
    metode_klasifikasi ENUM(
        'RULE_BASE',
    'REGEX',
    'SVM',
    'MANUAL'
    ),

    -- review manual --
    perlu_review BOOLEAN DEFAULT FALSE,
    kategori_id_koreksi BIGINT NULL,
    direview_oleh BIGINT NULL,
    direview_at DATETIME NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY(upload_id)
        REFERENCES upload_history(id),
    FOREIGN KEY(kategori_id)
        REFERENCES kategori(id),
    FOREIGN KEY(budget_id)
        REFERENCES budget(id),
    FOREIGN KEY(kategori_id_koreksi)
        REFERENCES kategori(id),
    FOREIGN KEY(direview_oleh)
        REFERENCES users(id),
    FOREIGN KEY(planning_detail_id)
        REFERENCES planning_detail(id)
);

-- klasifikasi log --
CREATE TABLE klasifikasi_log (

    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    pr_po_data_id BIGINT,

    layer TINYINT,

    method ENUM(
        'RULE_BASE',
        'REGEX',
        'SVM'
    ),
    berhasil BOOLEAN,

    kategori_hasil_id BIGINT,

    confidence_score DECIMAL(5,4),

    processing_time DECIMAL(10,4),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(pr_po_data_id)
        REFERENCES pr_po_data(id),

    FOREIGN KEY(kategori_hasil_id)
        REFERENCES kategori(id)

);

CREATE TABLE planning_header (

    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    periode VARCHAR(30) NOT NULL,
    user_id BIGINT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    status ENUM('UPLOADING', 'SUCCES' , 'FAILED') DEFAULT 'UPLOADING',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id)
        REFERENCES users(id)
);

CREATE TABLE planning_detail(
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    planning_header_id BIGINT NOT NULL,
    kategori_id BIGINT NOT NULL,
    month VARCHAR(10)NOT NULL,
    item VARCHAR(255) NOT NULL,
    planning_amount DECIMAL(18,2) NOT NULL,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY(planning_header_id)
        REFERENCES planning_header(id),
    FOREIGN KEY(kategori_id)
        REFERENCES kategori(id)
);
CREATE TABLE item_mapping (

    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    kategori_id BIGINT NULL,

    keyword VARCHAR(255) NOT NULL,

    planning_item VARCHAR(255) NOT NULL,

    priority INT DEFAULT 1,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY(kategori_id)
        REFERENCES kategori(id)
);
    

    
    
    