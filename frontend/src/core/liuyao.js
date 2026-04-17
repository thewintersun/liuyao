import { getBaZi, TIAN_GAN, DI_ZHI } from './calendar.js'
import { gua64, fushen_dict, gua_gong_wuxing_dict, biangua_liuqin_replace_dict } from './hexagramData.js'

export class Liuyao {
  constructor() {
    this.reset()

    // 六神天干映射 (与 iOS Liuyao.swift 完全一致)
    this.liushenMap = { "甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5 }
    this.liushencn = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]

    // 天干地支数值映射
    this.tianganNum = { "甲": 1, "乙": 2, "丙": 3, "丁": 4, "戊": 5, "己": 6, "庚": 7, "辛": 8, "壬": 9, "癸": 10 }
    this.dizhiNum = { "子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6, "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12 }
    this.kongwangzu = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
  }

  reset() {
    this.dgua = []
    this.ygua = []
    this.bbgua = []
    this.gua = []
    this.guastr = ""
    this.bguastr = ""
    this.kongwang_display = ""
    this.liushenlist = []
    this.tiangan_dizhi_list = []
    this.year = 0
    this.month = 0
    this.day = 0
    this.hour = 0
    this.ritian = ""
    this.ridi = ""
  }

  setDate(year, month, day, hour) {
    this.year = year
    this.month = month
    this.day = day
    this.hour = hour
  }

  _kongwang() {
    // 空亡计算 - 与 iOS Liuyao.swift _kongwang() 完全一致
    let dizhi_num = this.dizhiNum[this.ridi]
    const tiangan_num = this.tianganNum[this.ritian]
    if (dizhi_num <= tiangan_num) {
      dizhi_num += 12
    }
    const cha = dizhi_num - tiangan_num - 1
    this.kongwang_display = this.kongwangzu[cha - 1] + this.kongwangzu[cha]
  }

  _liushenf() {
    // 六神计算 - 与 iOS Liuyao.swift _liushenf() 完全一致
    let xu = this.liushenMap[this.ritian]
    this.liushenlist = []
    for (let i = 0; i < 6; i++) {
      this.liushenlist.push(this.liushencn[xu])
      xu = (xu + 1) % 6
    }
  }

  paipan(coinList) {
    // 排盘主函数 - 与 iOS Liuyao.swift paipan() 完全一致
    // coinList: [0-3, 0-3, ...] 6个值
    // 0=无背(老阴), 1=一背(阳), 2=二背(阴), 3=三背(老阳)

    // 获取八字
    const date = new Date(this.year, this.month - 1, this.day, this.hour)
    const bazi = getBaZi(date)
    this.tiangan_dizhi_list = bazi.map(([g, z]) => g + z)

    // 日天干、日地支
    this.ritian = bazi[2][0]
    this.ridi = bazi[2][1]

    // 计算空亡
    this._kongwang()

    // 硬币转爻象 (与 iOS 完全一致: 0→"4", 1→"1", 2→"2", 3→"3")
    this.ygua = []
    for (let i = 0; i < 6; i++) {
      if (coinList[i] === 0) this.ygua.push("4")       // 无背 = 老阴
      else if (coinList[i] === 1) this.ygua.push("1")   // 一背 = 阳
      else if (coinList[i] === 2) this.ygua.push("2")   // 二背 = 阴
      else this.ygua.push("3")                           // 三背 = 老阳
    }

    // 初始化本卦
    this.gua = [...this.ygua]
    this.dgua = []

    // 处理动爻 (与 iOS 完全一致)
    for (let i = 0; i < 6; i++) {
      if (this.ygua[i] === "3") {        // 老阳
        this.gua[i] = "1"                // 本卦中显示为阳爻
        this.dgua.push(String(i))        // 记录动爻位置
        this.dgua.push("1")              // 记录动爻类型
      } else if (this.ygua[i] === "4") { // 老阴
        this.gua[i] = "2"                // 本卦中显示为阴爻
        this.dgua.push(String(i))        // 记录动爻位置
        this.dgua.push("2")              // 记录动爻类型
      }
    }

    // gua中1为阳，2为阴
    this.guastr = this.gua.join("")

    // 根据动爻计算变卦 (与 iOS 完全一致)
    this.bbgua = [...this.gua]
    for (let i = 0; i < this.dgua.length; i += 2) {
      const pos = parseInt(this.dgua[i])
      if (this.dgua[i + 1] === "1") {   // 老阳变阴
        this.bbgua[pos] = "2"
      } else {                            // 老阴变阳
        this.bbgua[pos] = "1"
      }
    }
    this.bguastr = this.bbgua.join("")

    // 计算六神
    this._liushenf()
  }

  getMainGuaLiuqin() {
    const data = gua64[this.guastr]
    return data ? data.slice(0, 6) : []
  }

  getBianGuaLiuqin() {
    // 变卦六亲 - 与 iOS get_biangua_liuqin() 完全一致
    const bdata = gua64[this.bguastr]
    if (!bdata) return []
    const bliuqin = bdata.slice(0, 6)
    const guaWuxing = gua_gong_wuxing_dict[this.guastr] // 注意：用本卦的guastr

    const result = []
    for (let i = 0; i < 6; i++) {
      const item = bliuqin[i]
      const lastChar = item[item.length - 1] // 五行字
      const key = guaWuxing + " " + lastChar
      const replaceStr = biangua_liuqin_replace_dict[key]
      if (replaceStr) {
        result.push(replaceStr + item.substring(1))
      } else {
        result.push(item)
      }
    }
    return result
  }

  getFuShen() {
    const data = fushen_dict[this.guastr]
    return data ? data.slice(0, 6) : []
  }

  getLiuShenList() {
    return this.liushenlist
  }

  getDyaoDisplay() {
    // 与 iOS get_dyao_display() 完全一致: ["pos type", ...]
    const result = []
    for (let i = 0; i < this.dgua.length; i += 2) {
      const pos = this.dgua[i]
      const type = this.dgua[i + 1]
      result.push(pos + " " + (type === "1" ? "O" : "X"))
    }
    return result
  }

  getShiYaoWeizhi() {
    const data = gua64[this.guastr]
    return data ? parseInt(data[6]) - 1 : 0
  }

  getYingYaoWeizhi() {
    const data = gua64[this.guastr]
    return data ? parseInt(data[7]) - 1 : 0
  }

  getLiuHeLiuChong() {
    const data = gua64[this.guastr]
    return data ? data[8] : ""
  }

  getBianGuaLiuHeLiuChong() {
    const data = gua64[this.bguastr]
    return data ? data[8] : ""
  }

  getYouHunGuiHun() {
    const data = gua64[this.guastr]
    return data ? data[9] : ""
  }

  getBianGuaYouHunGuiHun() {
    const data = gua64[this.bguastr]
    return data ? data[9] : ""
  }

  getGuaGong() {
    const data = gua64[this.guastr]
    return data ? [data[10], data[11]] : ["", ""]
  }

  getBianGuaGong() {
    const data = gua64[this.bguastr]
    return data ? [data[10], data[11]] : ["", ""]
  }

  getKongWangDisplay() {
    return this.kongwang_display
  }

  getTimeCn() {
    return this.tiangan_dizhi_list[0] + "年" + this.tiangan_dizhi_list[1] + "月" +
           this.tiangan_dizhi_list[2] + "日" + this.tiangan_dizhi_list[3] + "时"
  }

  getTime() {
    return this.year + "年" + this.month + "月" + this.day + "日" + this.hour + "时"
  }

  getGuaXiangInfo() {
    // 与 iOS get_guaxiang_info() 完全一致
    const mainLiuqin = this.getMainGuaLiuqin()

    // dyao_display 格式与 iOS 一致: ["pos liuqin", ...]
    // iOS: "\(dgua[i]) \(type)" 但 getGuaXiangInfo 中没有额外转换
    // 查看 iOS 源码: guaxiang_info["dyao_display"] = get_dyao_display()
    // get_dyao_display 返回 ["0 O", "3 X"] 格式
    // 但后端 orgnize_data 解析时用 dyao_display[i].split(' ')[0] 只取位置
    // 实际上 iOS 的 GuaXiangViewController 中发送给后端的是:
    // dyao_display 带六亲信息: "pos+1 liuqin"
    // 需要再检查... 实际 iOS get_guaxiang_info 直接用 get_dyao_display() 返回 "pos O/X" 格式

    return {
      timecn: [this.getTimeCn()],
      time: [this.getTime()],
      kongwang: [this.kongwang_display],
      maingua_liuqin: [...mainLiuqin],
      biangua_liuqin: [...this.getBianGuaLiuqin()],
      fugua_liuqin: [...this.getFuShen()],
      liushen: [...this.liushenlist],
      maingua_gong: this.getGuaGong(),
      biangua_gong: this.getBianGuaGong(),
      maingua_liuchong: [this.getLiuHeLiuChong()],
      biangua_liuchong: [this.getBianGuaLiuHeLiuChong()],
      maingua_youhun: [this.getYouHunGuiHun()],
      biangua_youhun: [this.getBianGuaYouHunGuiHun()],
      dyao_display: this.getDyaoDisplay(),
      shiyao_weizhi: [String(this.getShiYaoWeizhi())],
      yingyao_weizhi: [String(this.getYingYaoWeizhi())]
    }
  }
}
