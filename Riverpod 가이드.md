# 🚀 Riverpod 공부

## 🤔 무엇인가?

### Riverpod = Provider 2.0
```dart
// Provider (기존)
ChangeNotifierProvider<AuthNotifier>(
  create: (context) => AuthNotifier(), // context 의존
  child: MyApp(),
)

// Riverpod (개선)
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(), // ref 사용, context 무관
);
```

### 핵심 개념: "강 위의 Provider"
- **River** (강) = 데이터의 흐름
- **Pod** (콩깍지) = 데이터를 감싸는 컨테이너
- 즉, **데이터가 강물처럼 흘러가며 앱 전체에 공급**

### Flutter 상태관리 진화 과정
```
setState() → Provider → Riverpod
(지역적)   → (의존적)  → (독립적)

setState: 위젯 내부에서만 사용
Provider: context에 의존적
Riverpod: context 독립적, 어디서나 사용 가능
```

### 🤔 왜 context 대신 ref를 사용했나?

#### Context의 문제점과 실제 문제 상황

##### 문제 1: 위젯 트리 밖에서 사용 불가 - 왜 문제인가? 🤯
```dart
// 실무 상황: 백그라운드 알림 처리
class PushNotificationService {
  static void handleNotification(Map<String, dynamic> data) {
    // 😱 위젯이 없는데 유저 정보가 필요함!
    // final user = Provider.of<User>(context); // context가 없어서 불가능!

    // 억지로 하려면...
    if (data['type'] == 'message') {
      // 유저 로그인 상태를 확인할 수 없어서
      // 모든 알림을 무조건 표시할 수밖에 없음 😢
      showNotification(data['message']);
    }
  }
}

// 또 다른 실무 상황: API 토큰 갱신
class TokenRefreshService {
  static Future<void> refreshExpiredToken() async {
    // 😱 토큰 저장소에 접근할 수 없음!
    // final storage = Provider.of<TokenStorage>(context); // 불가능!

    // 결국 직접 인스턴스를 만들어야 함 (의존성 주입 포기)
    final storage = TokenStorage(); // 하드코딩 😭
  }
}
```

##### 문제 2: context가 없는 곳에서는 접근 불가 - 실제 고통 😭
```dart
// 실무 상황: 전역 에러 핸들러
class GlobalErrorHandler {
  static void handleError(Object error) {
    // 😱 에러 로그를 서버에 보내고 싶은데...
    // final logger = Provider.of<LoggerService>(context); // context 없음!

    // 유저 정보도 함께 보내고 싶은데...
    // final user = Provider.of<User>(context); // 역시 불가능!

    // 결국 print만... 😢
    print('Error: $error');
  }
}

// 실무 상황: Dio Interceptor에서 토큰 처리
class AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    // 😱 토큰을 가져오고 싶은데 context가 없음!
    // final token = Provider.of<AuthService>(context).token; // 불가능!

    // 결국 하드코딩하거나 싱글톤 패턴 사용
    final token = AuthService.instance.token; // 안티패턴 😭
    options.headers['Authorization'] = 'Bearer $token';

    handler.next(options);
  }
}
```

##### 문제 3: InheritedWidget에 의존적 - 위젯 트리 구조의 제약 😵
```dart
// 실무 상황: 복잡한 위젯 트리에서 Provider 위치 문제
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: MultiProvider( // Provider가 여기 있음
        providers: [
          Provider<AuthService>(create: (_) => AuthService()),
        ],
        child: HomeScreen(),
      ),
    );
  }
}

class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(),
      body: TabBarView(
        children: [
          ProfileTab(),
          SettingsTab(),
        ],
      ),
    );
  }
}

class ProfileTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // ✅ 여기서는 Provider 접근 가능 (위젯 트리 안)
    final auth = Provider.of<AuthService>(context);
    return Text('User: ${auth.user?.name}');
  }
}

// 😱 문제 상황: 다이얼로그에서 Provider 접근
void showCustomDialog(BuildContext context) {
  showDialog(
    context: context,
    builder: (dialogContext) {
      // 😱 dialogContext는 새로운 context!
      // Provider에 접근할 수 없을 수도 있음!
      try {
        final auth = Provider.of<AuthService>(dialogContext); // 위험!
        return Text('User: ${auth.user?.name}');
      } catch (e) {
        return Text('Provider not found!'); // 에러 발생 가능
      }
    },
  );
}

// 😱 더 심각한 문제: Navigator로 이동한 화면
class LoginScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (newContext) {
              // 😱 newContext는 Provider 범위 밖일 수 있음!
              // Provider.of<AuthService>(newContext); // 에러 가능성
              return NewScreen();
            },
          ),
        );
      },
      child: Text('Navigate'),
    );
  }
}
```

#### ref의 장점
```dart
// ✅ Riverpod에서 ref 사용시
final authProvider = Provider<AuthService>((ref) => AuthService());

class MyWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider); // ref 사용
    return Text('Hello');
  }
}

// 위젯 외부에서도 사용 가능! 🎉
void someFunction(WidgetRef ref) {
  final auth = ref.read(authProvider); // 가능!
}

// 심지어 전역적으로도 가능
final container = ProviderContainer();
void globalFunction() {
  final auth = container.read(authProvider); // 어디서든 가능!
}
```

### 🌍 Riverpod이 어떻게 독립적이고 어디서나 사용 가능한가?

#### 핵심 비밀: ProviderContainer라는 마법 🪄
```dart
// Provider 방식의 제약
Provider 의존성: 위젯 트리 → InheritedWidget → context

// Riverpod의 자유로움
Riverpod 독립성: ProviderContainer (전역) → 어디서든 접근 가능
```

#### 1. ProviderContainer 시스템
```dart
// Riverpod의 핵심: ProviderContainer
final container = ProviderContainer();

// 위젯 트리 밖에서도 Provider 사용 가능
void main() {
  // 앱 시작 전에도 사용
  final auth = container.read(authProvider);
  auth.initialize();

  runApp(
    UncontrolledProviderScope(
      container: container,
      child: MyApp(),
    ),
  );
}

// 백그라운드 작업에서도 사용
class BackgroundService {
  static Future<void> syncData() async {
    final api = container.read(apiProvider); // 위젯 없이도 가능!
    await api.sync();
  }
}
```

#### 2. Context 없이 어디서든 접근
```dart
// ❌ Provider 방식 - context 필수
class NetworkService {
  void makeRequest(BuildContext context) { // context 필요
    final api = Provider.of<ApiClient>(context);
    api.get('/data');
  }
}

// ✅ Riverpod 방식 - ref만 있으면 OK
class NetworkService {
  final Ref ref;
  NetworkService(this.ref);

  void makeRequest() {
    final api = ref.read(apiProvider); // context 불필요!
    api.get('/data');
  }
}

// 또는 전역 컨테이너 사용
class NetworkService {
  void makeRequest() {
    final api = container.read(apiProvider); // 완전 독립적!
    api.get('/data');
  }
}
```

#### 3. 테스트에서도 독립적
```dart
void main() {
  test('비즈니스 로직 테스트 - 위젯 없이', () {
    // Provider 방식: 위젯 트리 필요
    // Riverpod 방식: 컨테이너만 있으면 OK

    final container = ProviderContainer(
      overrides: [
        apiProvider.overrideWith((ref) => MockApi()),
      ],
    );

    final authService = container.read(authServiceProvider);
    expect(authService.isLoggedIn, false); // 위젯 없이도 테스트 가능!

    container.dispose();
  });
}
```

## 🎯 왜 필요한가?

### 1. 전역 상태 관리
```dart
// ❌ StatefulWidget만 사용시
// 로그인 정보를 여러 화면에 전달하려면 props drilling 지옥
HomeScreen(user: user)
  → ProfileTab(user: user)
    → UserInfo(user: user)
      → Avatar(user: user)

// ✅ Riverpod 사용시
// 어디서든 바로 접근
final user = ref.watch(authProvider).user;
```

### 2. 의존성 주입
```dart
// ❌ 하드코딩된 의존성
class UserService {
  final ApiClient _api = ApiClient(); // 테스트하기 어려움
}

// ✅ Riverpod으로 의존성 주입
final apiProvider = Provider<ApiClient>((ref) => ApiClient());
final userServiceProvider = Provider<UserService>((ref) =>
  UserService(ref.watch(apiProvider)) // 자동 주입
);
```

### 3. 테스트 용이성
```dart
// 테스트에서 실제 API 대신 Mock 사용
testWidgets('로그인 테스트', (tester) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiProvider.overrideWith((ref) => MockApiClient()),
      ],
      child: LoginScreen(),
    ),
  );
});
```


## ✅ 장점
- **컴파일 타임 안전성**: 런타임 에러 방지
- **자동 dispose**: 메모리 누수 방지
- **의존성 추적**: Provider 간 관계 자동 관리
- **Hot reload 지원**: 개발 속도 향상

## ❌ 단점
- **학습 곡선**: Provider보다 복잡
- **보일러플레이트**: 코드량 증가
- **과도한 추상화**: 간단한 앱엔 오버킬

## 기본 사용법

### Provider 만들기
```dart
// 1. 서비스 Provider
final apiProvider = Provider<ApiService>((ref) => ApiService());

// 2. 상태 Provider
final counterProvider = StateProvider<int>((ref) => 0);

// 3. 복잡한 상태 Provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(),
);
```

### UI에서 사용하기
```dart
class MyWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // 상태 읽기
    final count = ref.watch(counterProvider);

    // 액션 호출
    return ElevatedButton(
      onPressed: () => ref.read(counterProvider.notifier).state++,
      child: Text('$count'),
    );
  }
}
```

### StateNotifier 패턴
```dart
@freezed
class AuthState with _$AuthState {
  factory AuthState({
    @Default(false) bool isLoading,
    User? user,
  }) = _AuthState;
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(AuthState());

  Future<void> login() async {
    state = state.copyWith(isLoading: true);
    // API 호출...
    state = state.copyWith(isLoading: false, user: user);
  }
}
```

## 핵심 규칙
- `ref.watch()` = 구독 (UI에서)
- `ref.read()` = 한번만 읽기 (액션에서)
- `state = state.copyWith()` = 상태 업데이트
- `.notifier` = 액션 메서드 접근

끝! 😴
