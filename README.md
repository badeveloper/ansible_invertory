<h3>Динамическая инвертаризация для Ansible из нескольких VmWare vCenter.</h3>


<h5>Использование :</h5>
   
    1. git clone http://iyurev@git.x5.ru/iyurev/ansible_invertory.git && cd ansible_invertory
    2. chmod +x  simple_deploy_invertory 
    3. Заполнить inv.yaml , нужно внести данные для подключения к каждому vCenter 
    3. Можно проверить работу: ansible -i  simple_deploy_invertory  -u support -m ping all

<h5>Зависимости: </h5> 

    1. Для ubuntu 16:04  нужно поставить пакет python-pyvmomi.
    2. Для RHEL можно поставить из pip : pip install pyvmomi
    
<h5>Примечания:</h5>

    У пользователя от ,которого запускается скрипт должен быть 
    прописан private key от связки ключей пользователя support .
    