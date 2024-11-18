#include <iostream>
#include <fstream>
#include <vector>
#include <iomanip> 
using namespace std;

class Robot {
protected:
    int batteryLife;
    int* cleaningArea;
    int* cleaningTime;
    int hiz[2];

public:
    virtual void move(int hedefX, int hedefY) = 0;
    Robot() {
        
        hiz[0] = 0;
        hiz[1] = 1;
        cleaningArea = new int;
		batteryLife = 100;
        cleaningTime = new int;
    }

    virtual ~Robot() {
        delete cleaningArea;
        delete cleaningTime;
    }
};

class RobotSweeper : protected Robot {
private:
		int *currentX;
		int *currentY;
		int *currentBatteryLife;
		int *x2;
		int *y2;
		int *paspas_suyu;	

public:
    RobotSweeper() : currentX(new int(0)), currentY(new int(0)), currentBatteryLife(new int(100)), paspas_suyu(new int(0)), x2(new int(0)), y2(new int(0)) { }
    ~RobotSweeper() {
        delete currentX;
        delete currentY;
        delete currentBatteryLife;
        delete x2;
        delete y2;
        delete paspas_suyu;
    }
  	int &cleaningtime_getir(){
		return *cleaningTime;
		}
	int &batterylife_getir(){
		return *currentBatteryLife;
		}

	void vacuum(){
			if (*currentBatteryLife <= 5) {
              	robotu_sarj_etme();}
            else{
			}
			}	
			
	void mop() {
    	if (*paspas_suyu > 0 && *currentBatteryLife > 5) {
        	if (hiz[0] == 1) {
            	*currentBatteryLife = (*currentBatteryLife) - (*currentBatteryLife * 0.02);
				*paspas_suyu -= 1;}
				
            else {
            	*currentBatteryLife = (*currentBatteryLife )- (*currentBatteryLife * 0.03);
				*paspas_suyu -= 1;}
        }
        else{
	        robotu_sarj_etme();
			}
    }

	void sarj_istasyonuna_gitme() {
    	*x2 = *currentX;
    	*y2 = *currentY;
    	*currentX = 0;
    	*currentY = 0;
		}
	void robotu_sarj_etme(){
		sarj_istasyonuna_gitme();
		*currentBatteryLife = 100;
		*cleaningTime +=10;
		(*currentX) = (*x2)  ; 
    	(*currentY) =(*y2) ; 
	}

	
	RobotSweeper& operator=(const RobotSweeper& n) {
   			*y2 = *n.y2;
   			*x2 = *n.x2;
   			*cleaningTime = *n.cleaningTime;
   			*paspas_suyu = *n.paspas_suyu;
        	*currentBatteryLife = *n.currentBatteryLife;
        	*currentX = *n.currentX;
        	*currentY = *n.currentY;
     		return *this;
   }
    void move(int x,int y) override {
		if(*currentBatteryLife <= 5){
			cout << "Hareket icin yeterli enerji yok" << endl;
			robotu_sarj_etme();
			}
		int x_mesafe = x - (*currentX);
		int y_mesafe = y - (*currentY);
		if(x_mesafe>0 || y_mesafe > 0) {
			(*currentY) += 1;
		}
		if(x_mesafe<0 || currentY < 0) {
			(*currentY) += 1;
		}
    	if (x_mesafe < 0) {
        	(*currentX) -= 1;
    	}
    	if (x_mesafe > 0) {
        (*currentX) += 1;
    	}
    	if (currentY < 0) {
        	(*currentY) -= 1;
    	}
    	if (currentY > 0) {
        	(*currentY) += 1;
    	}

		if (hiz[0] == 1) {
        	*currentBatteryLife = (*currentBatteryLife) - (*currentBatteryLife * 0.01);
        	*cleaningTime += 2;}		
    	else {
        	*currentBatteryLife = (*currentBatteryLife) - (*currentBatteryLife * 0.02);
			*cleaningTime += 1;
			}
			}

};
class House{
	public:
		int x;
		int y;
		House() : x(0), y(0) {}
		
};
class Room:public House{
public:
	int x1;
	int y1;
	int obstacleX;
	int obstacleY;
	Room() : x1(0), y1(0),obstacleX(0),obstacleY(0){}
	int getRoom() const {
        cout << "Oda Bilgisi:" << endl;
        cout << "Kordinatlar: (" << x1 << ", " << y1 << ")" << std::endl;
        cout << "Engel Kordinatlari: (" << obstacleX << ", " << obstacleY << ")" << std::endl;
        return x1 + y1 + obstacleX + obstacleY;
    }
};
class Area:public House{
public:
	int edgeX;
	int edgeY;
	Area() : edgeX(0), edgeY(0){}
	int getArea() const {
        std::cout << "Konum Bilgisi:" << std::endl;
        std::cout << "Engel Kordinatlari: (" << edgeX << ", " << edgeY << ")" << std::endl;
        return edgeX * edgeY;
    }
};
void harita_dosyasi_okuma(const std::string& dosyaadi, std::vector<Room>& odalar, std::vector<std::pair<int, int>>& engel) {
    ifstream inputFile(dosyaadi);
    string obje_turu;
    if (!inputFile) {
        cerr << "Dosya acilamadi !!" << endl;
        exit(EXIT_FAILURE);
    }

    while (inputFile >> obje_turu) {
        if (obje_turu == "Room") {
            Room oda;
            inputFile >> oda.x1 >> oda.y1 >> oda.obstacleX >> oda.obstacleY;
            odalar.push_back(oda);
        } else if (obje_turu == "Obstacle") {
            int engel_x;
			int engel_y;
            inputFile >> engel_x >> engel_y;
            engel.emplace_back(engel_x, engel_y);
        }
    }

    inputFile.close();
}


void cleanArea(RobotSweeper& robot, int ilk_x, int ilk_y, int son_x, int son_y, const vector<pair<int, int>>& engeller) {
    int& cleaningTime = robot.cleaningtime_getir();
    int& batteryLife = robot.batterylife_getir();

    int toplam_temizlenme_alani = (son_x - ilk_x + 1) * (son_y - ilk_y + 1);

    for (int x = ilk_x; x <= son_x; ++x) {
        for (int y = ilk_y; y <= son_y; ++y) {
            bool engel_kontrol = false;
            for (const auto& engel : engeller) {
                if (x == engel.first && y == engel.second) {
                    engel_kontrol = true;
                    break;
                }
            }

            if (!engel_kontrol) {
                if (batteryLife <= 5) {
                    cout << "Vacum icin yeterli enerji yok" << endl;
                    robot.robotu_sarj_etme();
                } else {
                    robot.move(x, y);
                    robot.vacuum();
                    robot.mop();
                }
            }
        }
    }

    cleaningTime = toplam_temizlenme_alani * 2;  // Assume 2 minutes for each unit area
    batteryLife -= toplam_temizlenme_alani;       // Assume 1 unit battery usage for each unit area

    batteryLife = max(batteryLife, 0);

    cout << "Rapor :" << endl;
    cout << "Temizlenenen Alan : " << toplam_temizlenme_alani << " metre^2" << endl;
    cout << "Temizlenme Suresi : " << cleaningTime << " dakika" << endl;
    cout << "Kalan sarj yuzdesi : " << batteryLife << "%" << endl;
    cout << "Karsilasilan Engel Sayisi :" << engeller.size() << endl;

    ofstream outFile("TemizlikRaporu.txt", ios::app);
    outFile << "Rapor :" << endl;
    outFile << "Temizlenenen Alan : " << toplam_temizlenme_alani << " metre^2" << endl;
    outFile << "Temizlenme Suresi : " << cleaningTime << " dakika" << endl;
    outFile << "Kalan sarj yuzdesi : " << batteryLife << "%" << endl;
    outFile << "Karsilasilan Engel Sayisi :" << engeller.size() << endl;
    for (const auto& engel : engeller) {
        outFile << "Engel Konumu : (" << engel.first << ", " << engel.second << ")" << endl;
    }
    outFile.close();

    
}






int kullanici_secimi() {
	int secim;
    cout << "Lutfen yapmak istediginiz islemi seciniz:\n";
    cout << "1. Genel Temizlik\n";
    cout << "2. Vacumlama\n";
    cout << "3. Paspaslama\n";
    cout << "4. Robotu sarj istasyonuna gitme\n";
	cout << "5. Robotu sarj etme\n";
    cout << "6.Hareket etme\n";
    cout << "0. Exit\n";
    cout << "Your choice: ";
    cin >> secim;
    return secim;
}

 





int main() {
	
  	vector<Room> odalar;
    vector<std::pair<int, int>> engeller;
    harita_dosyasi_okuma("Harita.txt", odalar, engeller);
    RobotSweeper robot1;
    int secim;
    int ilk_x, ilk_y, son_x, son_y,x,y;
    secim = kullanici_secimi();
    while(secim != 123456789){
    	
        switch (secim) {
            case 1: 
            
             	cout << "Enter the coordinates of the area to be cleaned (startX startY endX endY): ";
    			cin >> ilk_x >> ilk_y >> son_x >> son_y;
   			 	cleanArea(robot1, ilk_x, ilk_y, son_x, son_y, engeller);
    
                break;
            
            case 2:
                robot1.vacuum();
                break;
            case 3:
                robot1.mop();
                break;
            case 4:
                robot1.sarj_istasyonuna_gitme();
                break;
            case 5:
                robot1.robotu_sarj_etme();
                break;
            case 6:
            	cin >> x >> y ;
                robot1.move(x,y);
                break;
            case 0:
                cout << "Cikis yapiliyor.\n";
                
                break;
            default:
                cout << "Invalid choice. Try again.\n";
                break;
        }
        secim = kullanici_secimi();
        if(secim == 0){
        	secim = 123456789;
		}
        
	}
    

    
 

    return 0;
}